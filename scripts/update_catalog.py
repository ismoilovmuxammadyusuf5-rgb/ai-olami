"""Run with ``python -m scripts.update_catalog``; no keys or paid services."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import tempfile
from urllib.parse import urlsplit

from .catalog import AI_RE, canonical_url, merge_candidates, parse_feed
from .network import fetch
from .promotions import OFFER_RE, OFFICIAL_HOSTS, verify_promotion

LOG = logging.getLogger("ai-olami")
SOURCES = (
    {"name": "Product Hunt", "url": "https://www.producthunt.com/feed",
     "hosts": ["www.producthunt.com", "producthunt.com"], "kind": "discovery"},
    {"name": "OpenAI", "url": "https://openai.com/news/rss.xml",
     "hosts": ["openai.com", "www.openai.com"], "kind": "official"},
    {"name": "Google", "url": "https://blog.google/rss/",
     "hosts": ["blog.google", "www.blog.google"], "kind": "official"},
)


def _load(folder, name, key=None):
    path = folder / name
    if not path.exists():
        return {key: []} if key else {}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict) or (key and not isinstance(value.get(key), list)):
        raise ValueError(f"Invalid local data schema: {name}")
    return value


def _atomic_write(path, value):
    content = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    filename = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", dir=path.parent,
                                         prefix=".update-", suffix=".tmp", delete=False) as handle:
            filename = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(filename, path)
    finally:
        if filename and os.path.exists(filename):
            os.unlink(filename)


def _source_result(source, fetcher):
    report = {"name": source["name"], "url": source["url"], "status": "error", "count": 0}
    try:
        payload, final_url = fetcher(source["url"], allowed_hosts=source["hosts"])
        if (urlsplit(final_url).hostname or "").lower() not in source["hosts"]:
            raise ValueError("Feed redirected outside its allowlist")
        rows = parse_feed(payload, source["name"], source["url"])
        if source.get("kind") == "official":
            # Official evidence must remain on that publisher's host.
            rows = [row for row in rows if (urlsplit(row["url"]).hostname or "") in
                    {host.removeprefix("www.") for host in source["hosts"]}]
        report.update(status="ok", count=len(rows))
        LOG.info("%s: ok (%d entries)", source["name"], len(rows))
        return report, rows
    except Exception as error:
        report["error"] = type(error).__name__ + ": " + str(error)[:180]
        LOG.warning("%s: %s", source["name"], report["error"])
        return report, []


def _promotion_leads(existing, incoming, stamp):
    by_url = {}
    for row in existing:
        if not isinstance(row, dict):
            continue
        try:
            key = canonical_url(row.get("url", ""))
        except ValueError:
            continue
        by_url[key] = dict(row, url=key)
    for row in incoming:
        text = row.get("name", "") + " " + row.get("description", "")
        if not OFFER_RE.search(text) or not AI_RE.search(text):
            continue
        key = canonical_url(row["url"])
        if key in by_url:
            # A fresh lead cannot itself renew approval or replace evidence.
            by_url[key].update({k: row[k] for k in ("name", "description", "source", "source_url") if row.get(k)})
            by_url[key]["last_seen_at"] = stamp
        else:
            by_url[key] = dict(row, status="pending", found_at=stamp, last_seen_at=stamp)
    return list(by_url.values())


def _defer_promo(item, stamp, reason):
    # Queuing is not a verification attempt; preserving checked_at makes the
    # least-recently-checked ordering fair on the following hourly run.
    result = dict(item, status="pending", queued_at=stamp, reason=reason)
    for key in ("verified_at", "evidence", "price", "terms", "starts_at", "expires_at", "official_domain"):
        result.pop(key, None)
    return result


def run_update(data_dir, fetcher=None, now=None, sources=None):
    """Fetch independently, retain proven discovery data, revoke uncertain promos.

    Source outages are represented in the status file and do not make the site
    disappear. Invalid repository data is a real error and is never overwritten.
    ``fetcher`` and ``now`` are injectable for deterministic offline regression.
    """
    folder = Path(data_dir)
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    stamp = now.isoformat()
    fetcher = fetcher or fetch
    sources = list(SOURCES if sources is None else sources)
    old_ai = _load(folder, "ai-candidates.json", "candidates")
    old_approved = _load(folder, "approved-ai.json", "tools")
    old_promos = _load(folder, "promo-candidates.json", "promotions")
    old_status = _load(folder, "monitor-status.json")
    reports, incoming = [], []
    with ThreadPoolExecutor(max_workers=3) as pool:
        for report, rows in pool.map(lambda source: _source_result(source, fetcher), sources):
            reports.append(report)
            incoming.extend(rows)
    candidates = merge_candidates(old_ai["candidates"] + old_approved["tools"], incoming, stamp)
    approved = [row for row in candidates if row["status"] == "approved"]
    leads = _promotion_leads(old_promos["promotions"], incoming, stamp)
    # Unsupported leads are rejected without spending the page-fetch budget.
    eligible, unsupported = [], []
    for row in leads:
        allowed = OFFICIAL_HOSTS.get(row.get("source"), set())
        if (urlsplit(row.get("url", "")).hostname or "").lower() in allowed:
            eligible.append(row)
        else:
            unsupported.append(verify_promotion(row, fetcher, now))
    # Approvals are reverified first. Oldest unchecked pending leads rotate
    # through the bounded queue even if the same RSS items appear every hour.
    eligible.sort(key=lambda row: (row.get("status") != "approved", row.get("checked_at", ""), row.get("url", "")))
    selected, deferred = eligible[:12], eligible[12:2000]
    with ThreadPoolExecutor(max_workers=3) as pool:
        promotions = list(pool.map(lambda row: verify_promotion(row, fetcher, now), selected))
    promotions.extend(_defer_promo(row, stamp, "Tekshirish navbatida: bu ishga tushirishdagi manba limiti") for row in deferred)
    promotions.extend(unsupported[:2000])
    for row in promotions:
        row.setdefault("id", "promo-" + hashlib.sha256(row["url"].encode()).hexdigest()[:16])
    promotions.sort(key=lambda row: row["id"])
    for row in promotions:
        LOG.info("Promotion %s: %s (%s)", row["id"], row["status"], row.get("reason", ""))
    successes = sum(report["status"] == "ok" for report in reports)
    state = "ok" if reports and successes == len(reports) else "partial" if successes else "error"
    status = {
        "schema_version": 1, "last_run_at": stamp,
        "last_success_at": stamp if successes else old_status.get("last_success_at"),
        "overall_status": state, "sources": reports,
        "counts": {"approved": len(approved),
                   "pending": sum(row["status"] == "pending" for row in candidates),
                   "rejected": sum(row["status"] == "rejected" for row in candidates),
                   "promotions_approved": sum(row["status"] == "approved" for row in promotions)},
        "promotion_checks": [{key: row.get(key) for key in ("id", "url", "status", "reason", "checked_at")}
                             for row in promotions],
        "policy": "AI: explicit source function; promotions: official dated structured Offer; no paid API",
    }
    # All parsing and validation completes before any repository file is replaced.
    _atomic_write(folder / "ai-candidates.json", {"schema_version": 1, "updated_at": stamp, "candidates": candidates})
    _atomic_write(folder / "approved-ai.json", {"schema_version": 1, "updated_at": stamp, "tools": approved})
    _atomic_write(folder / "promo-candidates.json", {"schema_version": 1, "updated_at": stamp, "promotions": promotions})
    _atomic_write(folder / "monitor-status.json", status)
    LOG.info("Result=%s approved=%d pending=%d rejected=%d active_promotions=%d", state,
             len(approved), status["counts"]["pending"], status["counts"]["rejected"], status["counts"]["promotions_approved"])
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--offline", action="store_true", help="Rebuild from stored evidence; no network, promotions fail closed")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    fetcher = None
    if args.offline:
        def offline_fetch(url, allowed_hosts=None):
            raise OSError("Offline mode: no fresh source verification")
        fetcher = offline_fetch
    status = run_update(args.data_dir, fetcher=fetcher)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as handle:
            handle.write(f"AI Olami: **{status['overall_status']}**; checked {status['last_run_at']} UTC.\n\n")
            handle.write("| Source | Result | Entries |\n|---|---|---|\n")
            for source in status["sources"]:
                handle.write(f"| {source['name']} | {source['status']} | {source['count']} |\n")
            handle.write("\n" + ", ".join(f"{key}: {value}" for key, value in status["counts"].items()) + "\n")
            handle.write("\nA source outage retains the proven catalog; unverified promotions are hidden.\n")
    if status["overall_status"] != "ok":
        print("::warning::Some discovery sources were unavailable; see monitor-status.json and the job summary.")


if __name__ == "__main__":
    main()
