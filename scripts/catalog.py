"""RSS parsing, conservative AI classification, and stable product identities.

Approval here means that the source explicitly describes an AI function. It is
not an independent quality, price, safety, or availability endorsement.
"""
from __future__ import annotations

import hashlib
import html
import ipaddress
import re
import unicodedata
from html.parser import HTMLParser
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import xml.etree.ElementTree as ET

AI_RE = re.compile(r"\b(?:ai|artificial intelligence|machine learning|deep learning|llms?|gpt\w*|chatgpt|claude|gemini|copilot|generative)\b", re.I)
FUNCTION_RE = re.compile(r"\b(?:generat\w*|creat\w*|build\w*|writ\w*|transcrib\w*|summari[sz]\w*|automat\w*|analy[sz]\w*|assist\w*|chatbots?|copilots?|agents?|translat\w*|edit\w*|search\w*|answer\w*|cod(?:e|ing)|predict\w*|research\w*|design\w*|convert\w*|detect\w*)\b", re.I)
NEGATIVE_AI_RE = re.compile(r"\b(?:no ai|without ai|not (?:an? )?ai|ai[- ]free|non[- ]ai)\b", re.I)
COMPATIBILITY_RE = re.compile(r"\b(?:ai[- ](?:compatible|ready|friendly)|compatible with ai|for ai (?:tools|apps))\b", re.I)
AUDIENCE_RE = re.compile(r"\b(?:for|serving|used by|designed for)\s+(?:ai|artificial intelligence|llm)\s+(?:teams?|developers?|creators?|startups?|enthusiasts?|companies|researchers?)\b", re.I)
RESOURCE_RE = re.compile(r"\b(?:newsletters?|courses?|directories|directory|catalogs?|collections?|libraries|library|blogs?|communities|community|marketplaces?|tutorials?|ebooks?|prompt packs?|job boards?|news digest|curated list|roundup)\b", re.I)
NEWS_RE = re.compile(r"^(?:introducing|announcing|how we|why we|our |a new era|expanding|the future|what |meet the|behind |research:|updates? to)\b", re.I)

CATEGORY_RULES = (
    ("Video Generatsiya", r"\b(?:videos?|films?|animation|animated|clips?|text.to.video)\b"),
    ("Ovoz va Musiqa", r"\b(?:music|audio|voice|speech|songs?|sound|podcasts?|transcrib\w*|text.to.speech)\b"),
    ("Dasturlash va Kod", r"\b(?:code|coding|developer|programming|software|ide|debug\w*|pull requests?|app builder|build apps)\b"),
    ("Dizayn va 3D", r"\b(?:3d|design|presentations?|slides?|ui|ux|mockups?|logos?)\b"),
    ("Rasm va San’at", r"\b(?:images?|photos?|pictures?|artwork|art|illustrat\w*|text.to.image)\b"),
    ("Qidiruv va Tadqiqot", r"\b(?:search|research|papers?|knowledge|citations?|answers?|study|learning|tutor\w*)\b"),
    ("Katta Til Modellari", r"\b(?:chat\w*|writing|write|text|language|llms?|gpt\w*|claude|gemini|summari[sz]\w*|translat\w*)\b"),
    ("Avtomatlashtirish", r"\b(?:agents?|automat\w*|workflows?|assistants?|productivity|tasks?)\b"),
)
CATEGORIES = tuple(name for name, _ in CATEGORY_RULES)


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self.skip += 1
        elif tag in {"p", "br", "div", "li"}:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"} and self.skip:
            self.skip -= 1
        self.parts.append(" ")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def plain_text(value, limit=1500):
    parser = PlainText()
    parser.feed(str(value or ""))
    return " ".join(html.unescape("".join(parser.parts)).split())[:limit]


def canonical_url(value):
    """Canonicalize identity only; never invent an official product URL."""
    if not isinstance(value, str) or len(value) > 2048:
        raise ValueError("Invalid URL")
    parts = urlsplit(value.strip())
    host = (parts.hostname or "").lower().rstrip(".")
    if parts.scheme.lower() != "https" or not host or parts.username or parts.password:
        raise ValueError("A public HTTPS URL is required")
    try:
        if parts.port not in (None, 443):
            raise ValueError("Only HTTPS port 443 is allowed")
    except ValueError as error:
        raise ValueError("Invalid HTTPS port") from error
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal")) or "." not in host:
        raise ValueError("Private hosts are not allowed")
    try:
        if not ipaddress.ip_address(host).is_global:
            raise ValueError("Private addresses are not allowed")
    except ValueError as error:
        if "addresses" in str(error):
            raise
    host = host.removeprefix("www.")
    if not re.fullmatch(r"[a-z0-9.-]+", host):
        raise ValueError("Invalid hostname")
    path = re.sub(r"/{2,}", "/", parts.path).rstrip("/")
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in {"ref", "source", "fbclid", "gclid", "mc_cid", "mc_eid"}]
    return urlunsplit(("https", host, path, urlencode(sorted(query)), ""))


def normalize_name(value):
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return re.sub(r"[^\w]+", "", text)


def stable_id(url):
    return "ai-" + hashlib.sha256(canonical_url(url).encode()).hexdigest()[:16]


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _field(entry, *names):
    for wanted in names:
        for child in entry:
            if _local(child.tag) == wanted:
                return "".join(child.itertext()).strip()
    return ""


def parse_feed(payload, source, source_url):
    if not isinstance(payload, bytes) or len(payload) > 5_000_000:
        raise ValueError("Feed exceeds size limit")
    if re.search(br"<!\s*(?:DOCTYPE|ENTITY)", payload, re.I):
        raise ValueError("DTD and entity declarations are not supported")
    root = ET.fromstring(payload)
    if _local(root.tag) not in {"rss", "feed", "RDF"}:
        raise ValueError("Source is not an RSS or Atom feed")
    rows = []
    for entry in root.iter():
        if _local(entry.tag) not in {"item", "entry"}:
            continue
        links = [child for child in entry if _local(child.tag) == "link"]
        link = ""
        for child in links:
            if child.attrib.get("rel", "alternate") == "alternate":
                link = child.attrib.get("href") or "".join(child.itertext()).strip()
                if link:
                    break
        try:
            url = canonical_url(link)
        except ValueError:
            continue
        name = plain_text(_field(entry, "title"), 160)
        if not name:
            continue
        categories = [plain_text(child.get("term") or "".join(child.itertext()), 120)
                      for child in entry if _local(child.tag) == "category"]
        description = plain_text(_field(entry, "description", "summary", "content", "encoded"))
        # Product Hunt includes navigation after the tagline; it is not evidence.
        description = re.split(r"\b(?:Discussion\s*\||Discussion\s+|Read more\s*\|)", description, maxsplit=1, flags=re.I)[0].strip()
        rows.append({"name": name, "url": url, "description": description,
                     "source": source, "source_url": source_url,
                     "categories": categories,
                     "published_at": _field(entry, "published", "pubDate", "updated")[:100]})
        if len(rows) >= 150:
            break
    return rows


def classify_ai(item):
    name = plain_text(item.get("name", ""), 160)
    description = plain_text(item.get("description", ""))
    text = f"{name} {description}"
    if not description:
        return "pending", "AI vazifasini tasdiqlovchi tavsif yetishmaydi", None
    if NEGATIVE_AI_RE.search(text):
        return "rejected", "Manba mahsulotni AI bo‘lmagan vosita deb tavsiflaydi", None
    if not AI_RE.search(text):
        return "rejected", "AI funksiyasi haqida aniq dalil yo‘q", None
    cleaned = AUDIENCE_RE.sub("", COMPATIBILITY_RE.sub("", text))
    if not AI_RE.search(cleaned):
        return "pending", "AI bilan moslik AI funksiyasi ekanini tasdiqlamaydi", None
    if item.get("source") in {"OpenAI", "Google"} or NEWS_RE.search(name):
        return "pending", "Yangilik maqolasi: alohida mahsulot ekanini tekshirish kerak", None
    if RESOURCE_RE.search(text):
        return "pending", "Resurs, to‘plam yoki yangilik: amaliy AI mahsuloti ekanini alohida tekshirish kerak", None
    # Category metadata alone, a product name, and marketing adjectives never pass.
    if not FUNCTION_RE.search(description) or not AI_RE.search(text):
        return "pending", "AI vazifasi yetarlicha aniq tavsiflanmagan", None
    # One phrase must tie AI to an actual function. Unrelated AI marketing in
    # another sentence cannot turn ordinary software into an AI product.
    related = False
    for phrase in re.split(r"[.!?;\n]+", cleaned):
        signals = list(AI_RE.finditer(phrase))
        functions = list(FUNCTION_RE.finditer(phrase))
        if any(abs(signal.start() - function.start()) <= 120
               for signal in signals for function in functions):
            related = True
            break
    if not related:
        return "pending", "AI va mahsulot vazifasi bir ifodada bog‘lanmagan", None
    for category, expression in CATEGORY_RULES:
        if re.search(expression, text, re.I):
            return "approved", "Manbada AI funksiyasi aniq tavsiflangan", category
    return "pending", "AI vazifasi yoki kategoriyasi noaniq", None


def identity_keys(item):
    try:
        url = canonical_url(item.get("url", ""))
    except ValueError:
        return set()
    parts = urlsplit(url)
    keys = {"url:" + url}
    name = normalize_name(item.get("name", ""))
    if name:
        # Same-name tools on unrelated domains are not automatically merged.
        keys.add(f"name:{parts.hostname}:{name}")
    match = re.fullmatch(r"/(?:posts|products)/([^/]+)", parts.path)
    if parts.hostname == "producthunt.com" and match:
        keys.add("ph:" + match.group(1))
    return keys


def merge_candidates(existing, incoming, now):
    records = []
    index = {}
    incoming_ids = set()
    for item, fresh in [(x, False) for x in existing] + [(x, True) for x in incoming]:
        if not isinstance(item, dict):
            continue
        keys = identity_keys(item)
        if not keys:
            continue
        match = next((index[k] for k in sorted(keys) if k in index), None)
        if match is None:
            record = dict(item)
            record["url"] = canonical_url(item["url"])
            record["id"] = item.get("id") or stable_id(record["url"])
            record.setdefault("found_at", now)
            records.append(record)
            match = len(records) - 1
        else:
            record = records[match]
            # New observations enrich old names-only records without destroying
            # valid evidence when a truncated/empty feed entry is encountered.
            for key in ("name", "description", "source", "source_url", "categories", "published_at"):
                if item.get(key):
                    record[key] = item[key]
        if fresh:
            record["last_seen_at"] = now
            incoming_ids.add(record["id"])
        for key in keys | identity_keys(record):
            index[key] = match
    for record in records:
        status, reason, category = classify_ai(record)
        # Legacy approved flags are not proof: every record must satisfy rules.
        record.update(status=status, reason=reason)
        if status == "approved":
            record["category"] = category
            record.setdefault("approved_at", now)
            record["evidence"] = {"source_url": record.get("source_url") or record["url"],
                                  "excerpt": record.get("description", ""),
                                  "rule": "explicit-ai-function-v1"}
        else:
            record.pop("approved_at", None)
            record.pop("evidence", None)
            record.pop("category", None)
    # Keep all approved records; bound unreviewed/rejected history by recency.
    approved = [row for row in records if row["status"] == "approved"]
    others = sorted((row for row in records if row["status"] != "approved"),
                    key=lambda row: (row.get("last_seen_at", row.get("found_at", "")), row["id"]), reverse=True)[:2000]
    return sorted(approved + others, key=lambda row: (row.get("found_at", ""), row["id"]))
