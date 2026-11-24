"""Validate the public data contract before committing or deploying it."""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlsplit

from .catalog import CATEGORIES, canonical_url
from .promotions import OFFICIAL_HOSTS, aware_date


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(name):
    value = json.loads((Path('data') / name).read_text(encoding='utf-8'))
    require(isinstance(value, dict) and value.get('schema_version') == 1,
            f'{name}: unsupported schema')
    return value


def main():
    now = datetime.now(timezone.utc)
    data = load('approved-ai.json')
    aware_date(data['updated_at'])
    require(isinstance(data.get('tools'), list), 'tools must be a list')
    ids, urls = set(), set()
    for tool in data['tools']:
        require(tool.get('status') == 'approved', 'Only approved tools may be exported')
        require(tool.get('name') and tool.get('description') and tool.get('source'), 'Tool metadata missing')
        require(tool.get('category') in CATEGORIES, 'Unknown category')
        url = canonical_url(tool['url'])
        canonical_url(tool['source_url'])
        aware_date(tool['approved_at'])
        require(tool.get('id') and tool['id'] not in ids and url not in urls, 'Duplicate tool identity')
        ids.add(tool['id'])
        urls.add(url)
        proof = tool.get('evidence', {})
        require(proof.get('excerpt') == tool['description'] and proof.get('source_url'), 'Missing discovery evidence')
        canonical_url(proof['source_url'])
    promos = load('promo-candidates.json')
    require(isinstance(promos.get('promotions'), list), 'promotions must be a list')
    for promo in promos['promotions']:
        require(promo.get('status') in {'approved', 'pending', 'rejected', 'expired'}, 'Invalid promotion status')
        if promo['status'] != 'approved':
            continue
        allowed = {host.removeprefix('www.') for host in OFFICIAL_HOSTS.get(promo.get('source'), set())}
        url = canonical_url(promo['url'])
        require(urlsplit(url).hostname in allowed and promo.get('official_domain') == urlsplit(url).hostname,
                'Promotion must link to its configured official host')
        proof = promo.get('evidence', {})
        require(canonical_url(proof['url']) == url, 'Promotion evidence URL mismatch')
        for field in ('price', 'terms', 'starts_at', 'expires_at'):
            require(isinstance(promo.get(field), str) and promo[field] and proof.get(field) == promo[field],
                    f'Promotion evidence mismatch: {field}')
        start, end, verified = map(aware_date, (promo['starts_at'], promo['expires_at'], promo['verified_at']))
        require(start <= now < end and start < end, 'Promotion is not currently active')
        require(now - timedelta(hours=24) <= verified <= now + timedelta(minutes=1), 'Promotion verification is stale')
        require(promo.get('type') in {'trial', 'bonus', 'discount'}, 'Unknown promotion type')
    status = load('monitor-status.json')
    aware_date(status['last_run_at'])
    require(status.get('overall_status') in {'ok', 'partial', 'error'}, 'Invalid monitor status')
    require(isinstance(status.get('sources'), list), 'Source status missing')
    require(status['counts']['approved'] == len(data['tools']), 'Approved tool count mismatch')
    print(f'Public data valid: {len(data["tools"])} discovered tools, '
          f'{sum(p["status"] == "approved" for p in promos["promotions"])} active promotions')


if __name__ == '__main__':
    main()
