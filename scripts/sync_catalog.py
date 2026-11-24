#!/usr/bin/env python3
"""Build an attributed directory cache, without inventing products or metrics.

Only the Python standard library is required. Source verification dates belong
to the source, not to AI Olami. A failed source retains its prior records; a
missing initial 1500-record catalogue or a large regression stops publication.
"""
from __future__ import annotations

import csv
from datetime import date, datetime, timezone
import html
import io
import ipaddress
import json
import os
from pathlib import Path
import re
import sys
import unicodedata
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "data" / "ai-olami-tools.json"
MIN_TOOLS = 1500
MAX_BYTES = 24_000_000
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
SOURCES = {
    "AGIPicks": {
        "data_url": "https://agipicks.com/data/tools.json",
        "url": "https://agipicks.com/data/",
        "attribution": "Data: AGIPicks, CC BY 4.0",
        "format": "json",
    },
    "TiorAI": {
        "data_url": "https://raw.githubusercontent.com/tioraicom/ai-tools-dataset/main/data/ai-tools.json",
        "url": "https://github.com/tioraicom/ai-tools-dataset",
        "attribution": "Data: TiorAI, CC BY 4.0",
        "format": "json",
    },
    "AIToolBuzz": {
        "data_url": "https://raw.githubusercontent.com/devadigax/aitoolbuzz-dataset/main/data/Complete%20AI%20Tools%20Dataset%202025%20-%2016763%20Tools%20from%20AIToolBuzz.csv",
        "url": "https://github.com/devadigax/aitoolbuzz-dataset",
        "attribution": "Data: AIToolBuzz.com, compiled by Devadigax, CC BY 4.0",
        "format": "csv",
    },
}
CATEGORIES = (
    "Katta Til Modellari", "Rasm va San’at", "Video Generatsiya",
    "Ovoz va Musiqa", "Dasturlash va Kod", "Qidiruv va Tadqiqot",
    "Dizayn va 3D", "Avtomatlashtirish",
)
BLOCKED_HOSTS = {"example.com", "example.org", "example.net", "localhost", "aitoolbuzz.com", "agipicks.com"}
TRACKING_KEYS = {"ref", "affiliate", "aff", "fbclid", "gclid"}
DEAD_STATUS = re.compile(r"\b(?:error|not found|inactive|dead|unavailable|closed|retired|404|503|500)\b", re.I)


class SourceRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlsplit(newurl)
        if parsed.scheme != "https" or parsed.hostname != urllib.parse.urlsplit(req.full_url).hostname:
            raise ValueError("Source redirected outside its HTTPS host")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download(url: str, limit: int = MAX_BYTES) -> bytes:
    request = urllib.request.Request(url, headers={
        "User-Agent": "AI-Olami-directory/3.0 (+https://ismoilovmuxammadyusuf5-rgb.github.io/ai-olami/)",
        "Accept-Encoding": "identity",
    })
    with urllib.request.build_opener(SourceRedirect()).open(request, timeout=60) as response:
        content = response.read(limit + 1)
    if not content or len(content) > limit:
        raise ValueError("External data is empty or exceeds size limit")
    return content


def clean_text(value, limit=550):
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", " ", value))).strip()[:limit]


def clean_url(value):
    if not isinstance(value, str) or len(value) > 2000 or any(c.isspace() for c in value.strip()):
        return ""
    value = value.strip()
    if value.startswith("www."):
        value = "https://" + value
    if value.startswith("http://"):
        value = "https://" + value[7:]
    try:
        parsed = urllib.parse.urlsplit(value)
        host = (parsed.hostname or "").lower().rstrip(".")
        host = host.encode("idna").decode("ascii")
        if parsed.scheme != "https" or not host or "." not in host or parsed.username or parsed.password or parsed.port not in (None, 443):
            return ""
        if any(host == x or host.endswith("." + x) for x in BLOCKED_HOSTS) or host.endswith((".local", ".internal", ".localhost")):
            return ""
        try:
            ipaddress.ip_address(host)
            return ""  # Official product links must use a public domain name.
        except ValueError:
            pass
        if not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", host):
            return ""
        query = sorted((k, v) for k, v in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
                       if k.lower() not in TRACKING_KEYS and not k.lower().startswith("utm_"))
        return urllib.parse.urlunsplit(("https", host, parsed.path or "/", urllib.parse.urlencode(query), ""))
    except (ValueError, UnicodeError):
        return ""


def canonical_url(value):
    cleaned = clean_url(value)
    if not cleaned:
        return ""
    parsed = urllib.parse.urlsplit(cleaned)
    return urllib.parse.urlunsplit(("https", parsed.netloc.removeprefix("www."), parsed.path.rstrip("/"), parsed.query, ""))


def normalize_name(value):
    return "".join(c for c in unicodedata.normalize("NFKC", value).casefold() if c.isalnum())


def source_date(value):
    if not isinstance(value, str):
        return ""
    try:
        if len(value) == 10:
            return date.fromisoformat(value).isoformat()
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value if parsed.tzinfo is not None else ""
    except ValueError:
        return ""


def category_of(category, task="", description=""):
    if category in CATEGORIES:
        return category
    value = " ".join((category, task)).casefold()
    for pattern, category_name in (
        (r"3d|design|presentation|slide|logo|graphics|ui/ux|interior", CATEGORIES[6]),
        (r"video|animation|film|movie", CATEGORIES[2]),
        (r"image|photo|picture|art|drawing|visual|illustrat", CATEGORIES[1]),
        (r"music|audio|speech|voice|sound|transcrip|podcast", CATEGORIES[3]),
        (r"program|coding|develop|code|software|devops|app build", CATEGORIES[4]),
        (r"research|science|search|academic|education|learning|data|analytic|seo|knowledge", CATEGORIES[5]),
        (r"chat|writing|text|language|translation|llm|conversation|summari", CATEGORIES[0]),
    ):
        if re.search(pattern, value):
            return category_name
    return CATEGORIES[7]  # Editorial grouping, not an externally verified taxonomy.


def normalize(record, source):
    if not isinstance(record, dict) or source not in SOURCES:
        return None
    row = {re.sub(r"[^a-z0-9]", "", str(k).casefold()): v for k, v in record.items()}

    def get(*keys):
        for key in keys:
            value = row.get(re.sub(r"[^a-z0-9]", "", key.casefold()))
            if value is not None and value != "" and str(value).strip().lower() not in ("nan", "none", "null"):
                return value
        return ""

    if source == "AGIPicks" and record.get("retired"):
        return None
    raw_name = get("name", "tool_name")
    if not isinstance(raw_name, str) or "\n" in raw_name or len(raw_name.strip()) > 140:
        return None
    name = clean_text(raw_name, 140)
    official = clean_url(get("official_url", "website", "officialwebsite", "websiteurl"))
    if len(name) < 2 or not normalize_name(name) or not official:
        return None
    if DEAD_STATUS.search(str(get("Website Status", "Status"))):
        return None
    description = clean_text(get("short_description", "description", "primarytask", "task"))
    category = clean_text(get("source_category", "primary_category", "category"), 100)
    task = clean_text(get("Task", "Primary Task"), 100)
    pricing = get("pricing_model", "PricingModel")
    if isinstance(pricing, str):
        pricing = re.split(r"[,;/]", pricing)
    tiers = [clean_text(v, 60) for v in pricing if isinstance(v, str) and v.strip()] if isinstance(pricing, list) else []
    # The historical CSV has no current price evidence. Unknown is not Free.
    if source == "AIToolBuzz":
        tiers = []
    verified = source_date(get("verifiedAt", "last_verified")) if source != "AIToolBuzz" else ""
    free_plan = get("freePlan", "free_plan")
    return {
        "name": name,
        "official_url": official,
        "primary_category": category_of(category, task, description),
        "source_category": category,
        "short_description": description,
        "pricing_model": tiers[:4],
        "free_plan": free_plan if isinstance(free_plan, bool) and source != "AIToolBuzz" else None,
        "open_source": get("open_source") is True,
        "source": source,
        "source_url": SOURCES[source]["url"],
        "license": "CC-BY-4.0",
        "license_url": LICENSE_URL,
        "source_date": verified,
        "last_verified": verified,
    }


def parse_source(content, source):
    text = content.decode("utf-8-sig")
    if SOURCES[source]["format"] == "csv":
        reader = csv.DictReader(io.StringIO(text, newline=""))
        if not reader.fieldnames or "name" not in {x.casefold() for x in reader.fieldnames}:
            raise ValueError("Source CSV has no Name column")
        rows = list(reader)
    else:
        doc = json.loads(text)
        rows = doc.get("tools") if isinstance(doc, dict) else doc
    if not isinstance(rows, list) or not rows or not all(isinstance(row, dict) for row in rows):
        raise ValueError("Source did not contain a nonempty record list")
    return [item for row in rows if (item := normalize(row, source)) is not None]


def dedupe(rows):
    names, urls, result = set(), set(), []
    for item in rows:
        name, url = normalize_name(item["name"]), canonical_url(item["official_url"])
        if not name or not url or name in names or url in urls:
            continue
        names.add(name)
        urls.add(url)
        result.append(item)
    return sorted(result, key=lambda item: (item["name"].casefold(), item["source"]))


def read_cache(destination):
    if not destination.exists():
        return None
    document = json.loads(destination.read_text(encoding="utf-8"))
    validate_document(document)
    return document


def validate_document(document):
    if not isinstance(document, dict) or document.get("schema_version") != 1:
        raise ValueError("Unknown catalogue schema")
    rows = document.get("tools")
    if not isinstance(rows, list) or len(rows) < MIN_TOOLS:
        raise ValueError("Existing catalogue has fewer than 1500 records")
    for row in rows:
        if not isinstance(row, dict) or row.get("source") not in SOURCES or not isinstance(row.get("name"), str) or not clean_url(row.get("official_url")):
            raise ValueError("Existing catalogue is invalid")
        if (row.get("primary_category") not in CATEGORIES or not isinstance(row.get("short_description"), str)
                or not isinstance(row.get("pricing_model"), list) or not all(isinstance(value, str) for value in row["pricing_model"])
                or not isinstance(row.get("open_source"), bool) or row.get("source_url") != SOURCES[row["source"]]["url"]
                or row.get("license") != "CC-BY-4.0" or row.get("license_url") != LICENSE_URL):
            raise ValueError("Existing catalogue has invalid provenance or fields")
        for field in ("source_date", "last_verified", "first_seen_at"):
            if row.get(field) and not source_date(row[field]):
                raise ValueError("Existing catalogue has invalid dates")
    if len(dedupe(rows)) != len(rows):
        raise ValueError("Existing catalogue contains duplicate products")
    actual = {source: sum(row["source"] == source for row in rows) for source in SOURCES}
    if document.get("sources") != actual:
        raise ValueError("Catalogue source counters do not match actual unique rows")
    return {"count": len(rows), "sources": actual}


def sync(destination=DEST, fetcher=download, now=None):
    now = now or datetime.now(timezone.utc).isoformat()
    previous = read_cache(destination)
    old_rows = previous["tools"] if previous else []
    gathered, source_status = [], {}
    for source, spec in SOURCES.items():
        try:
            rows = parse_source(fetcher(spec["data_url"]), source)
            if not rows:
                raise ValueError("No usable source records")
            source_status[source] = {"status": "fetched", "records": len(rows)}
        except Exception as error:
            rows = [row for row in old_rows if row["source"] == source]
            source_status[source] = {"status": "cached" if rows else "unavailable", "records": len(rows), "error": type(error).__name__}
            print(f"{source}: source unavailable ({type(error).__name__}); retained {len(rows)} cached records", file=sys.stderr)
        gathered.extend(rows)
    tools = dedupe(gathered)
    if len(tools) < MIN_TOOLS:
        if previous:
            print(f"Retaining previous catalogue: only {len(tools)} usable records")
            return {"retained": True, "count": len(old_rows), "sources": source_status}
        raise ValueError(f"Only {len(tools)} authentic source records; at least {MIN_TOOLS} required for initial publication")
    if previous and len(tools) < len(old_rows) * 0.95:
        print("Retaining previous catalogue: unexpected source regression greater than 5%")
        return {"retained": True, "count": len(old_rows), "sources": source_status}
    first_seen = {canonical_url(row["official_url"]): row.get("first_seen_at", previous.get("updated_at", now)) for row in old_rows}
    for item in tools:
        item["first_seen_at"] = first_seen.get(canonical_url(item["official_url"]), now)
    if previous and previous.get("tools") == tools:
        print(f"Unchanged catalogue: {len(tools)} unique source records")
        return {"retained": True, "count": len(tools), "sources": source_status}
    counts = {source: sum(item["source"] == source for item in tools) for source in SOURCES}
    document = {
        "schema_version": 1,
        "updated_at": now,
        "source_note": "Attributed directory records, deduplicated and grouped into AI Olami categories. Product links and source-reported pricing may be outdated; not independently live-verified by AI Olami.",
        "sources": counts,
        "source_status": source_status,
        "attributions": [{"name": source, "url": spec["url"], "data_url": spec["data_url"], "attribution": spec["attribution"], "license": "CC-BY-4.0", "license_url": LICENSE_URL} for source, spec in SOURCES.items()],
        "tools": tools,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    temporary.replace(destination)
    print(f"Saved {len(tools)} unique source records: {counts}")
    return {"retained": False, "count": len(tools), "sources": source_status}


def main():
    try:
        if sys.argv[1:] not in ([], ["--check"]):
            raise ValueError("Usage: python -m scripts.sync_catalog [--check]")
        if sys.argv[1:] == ["--check"]:
            document = read_cache(DEST)
            if document is None:
                raise ValueError("Catalogue JSON is missing")
            result = validate_document(document)
            summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
            if summary_path:
                lines = ["## AI Olami catalogue", "", f"Unique attributed source records: **{result['count']}**", "", "| Source | Unique records |", "| --- | ---: |"]
                lines.extend(f"| [{source}]({SOURCES[source]['url']}) | {count} |" for source, count in result["sources"].items())
                lines.extend(["", "Source-reported directory data; product availability and pricing are not independently verified by AI Olami.", ""])
                with open(summary_path, "a", encoding="utf-8") as summary:
                    summary.write("\n".join(lines))
        else:
            result = sync()
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ValueError, OSError) as error:
        print(f"Catalogue not published: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
