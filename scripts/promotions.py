"""Fail-closed promotion verification from explicit official Offer metadata.

RSS keywords discover a lead, never prove that an offer is current. There is no
natural-language date/price guessing. Unsupported formats stay pending.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from urllib.parse import urlsplit

from .catalog import AI_RE, canonical_url, normalize_name, plain_text

OFFICIAL_HOSTS = {
    "OpenAI": {"openai.com", "www.openai.com"},
    "Google": {"blog.google", "www.blog.google"},
}
OFFER_RE = re.compile(r"\b(?:free trials?|free credits?|bonus credits?|discount|promo codes?|limited.time offer|\d{1,3}\s*%\s*off)\b", re.I)


def aware_date(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?(?:Z|[+-]\d\d:\d\d)", value):
        raise ValueError("Explicit date, time and timezone are required")
    date = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if date.utcoffset() is None:
        raise ValueError("Timezone is required")
    return date


class StructuredData(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.active = False
        self.current = []
        self.documents = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script" and attrs.get("type", "").lower().split(";")[0].strip() == "application/ld+json":
            self.active = True
            self.current = []

    def handle_data(self, data):
        if self.active:
            self.current.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.active:
            self.active = False
            if len(self.documents) < 50:
                self.documents.append("".join(self.current))


def _objects(value, depth=0):
    if depth > 16:
        return
    if isinstance(value, dict):
        yield value
        for child in list(value.values())[:100]:
            yield from _objects(child, depth + 1)
    elif isinstance(value, list):
        for child in value[:100]:
            yield from _objects(child, depth + 1)


def _offers(payload):
    if len(payload) > 5_000_000:
        raise ValueError("Official page exceeds size limit")
    parser = StructuredData()
    parser.feed(payload.decode("utf-8", errors="replace"))
    for document in parser.documents:
        try:
            data = json.loads(document)
        except (ValueError, RecursionError):
            continue
        for obj in _objects(data):
            types = obj.get("@type", [])
            if isinstance(types, str):
                types = [types]
            if "Offer" in types:
                yield obj


def _text(value):
    # Required conditions are never truncated: omitted text could contain an
    # eligibility exclusion, auto-renewal charge, or payment-card requirement.
    if not isinstance(value, str) or len(value) > 2000:
        return ""
    return plain_text(value, 2000)


def _fail(item, status, reason, now):
    result = dict(item)
    result.update(status=status, reason=reason, checked_at=now.isoformat())
    for key in ("verified_at", "evidence", "price", "terms", "starts_at", "expires_at", "official_domain"):
        result.pop(key, None)
    return result


def verify_promotion(item, fetcher, now):
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    allowed = OFFICIAL_HOSTS.get(item.get("source"), set())
    original_url = item.get("url", "")
    try:
        url = canonical_url(original_url)
        host = (urlsplit(original_url).hostname or "").lower()
        if host not in allowed:
            return _fail(item, "rejected", "Rasmiy manba domeni tasdiqlanmadi", now)
    except (TypeError, ValueError):
        return _fail(item, "rejected", "Yaroqli rasmiy HTTPS manzil yo‘q", now)
    try:
        payload, final_url = fetcher(original_url, allowed_hosts=allowed)
        final = canonical_url(final_url)
        final_host = (urlsplit(final_url).hostname or "").lower()
        if final_host not in allowed:
            return _fail(item, "pending", "Rasmiy sahifa boshqa domenga yo‘naltirdi", now)
        offers = list(_offers(payload))
    except Exception as error:
        return _fail(item, "pending", "Rasmiy sahifani qayta tekshirib bo‘lmadi: " + type(error).__name__, now)
    target_name = normalize_name(item.get("name", ""))
    for offer in offers:
        offer_name = _text(offer.get("name"))
        offered = offer.get("itemOffered", {})
        offered_name = _text(offered.get("name")) if isinstance(offered, dict) else ""
        if not target_name or target_name not in {normalize_name(offer_name), normalize_name(offered_name)}:
            continue
        name = offer_name or offered_name
        description = _text(offer.get("description"))
        eligibility = _text(offer.get("eligibleCustomerType"))
        if not AI_RE.search(" ".join((name, description, offered_name))):
            continue
        if not description or not eligibility:
            continue
        if str(offer.get("availability", "")).rsplit("/", 1)[-1] not in {"InStock", "LimitedAvailability"}:
            continue
        try:
            raw_price = offer["price"]
            if isinstance(raw_price, bool) or not isinstance(raw_price, (str, int, float)):
                continue
            amount = Decimal(str(raw_price))
            currency = str(offer["priceCurrency"])
            if not amount.is_finite() or amount < 0 or not re.fullmatch(r"[A-Z]{3}", currency):
                continue
            # Preserve exact official timestamps, including their stated zone.
            starts_at = offer["validFrom"]
            expires_at = offer.get("priceValidUntil", offer.get("validThrough"))
            start, end = aware_date(starts_at), aware_date(expires_at)
            if any(aware_date(offer[field]) != end for field in
                   ("priceValidUntil", "validThrough", "availabilityEnds") if field in offer):
                continue
            if "availabilityStarts" in offer and aware_date(offer["availabilityStarts"]) != start:
                continue
            if end <= start:
                continue
        except (KeyError, TypeError, ValueError, InvalidOperation):
            continue
        if end <= now:
            return _fail(item, "expired", "Rasmiy manbaga ko‘ra aksiya muddati tugagan", now)
        if start > now:
            return _fail(item, "pending", "Aksiya hali boshlanmagan", now)
        kind = item.get("type")
        if kind not in {"trial", "bonus", "discount"}:
            if re.search(r"\btrial\b", description + " " + name, re.I):
                kind = "trial"
            elif re.search(r"\bcredits?\b", description + " " + name, re.I):
                kind = "bonus"
            elif re.search(r"\b(?:discount|%\s*off)\b", description + " " + name, re.I):
                kind = "discount"
            else:
                continue
        kind_evidence = description + " " + name
        required_word = {"trial": r"\btrial\b", "bonus": r"\bcredits?\b",
                         "discount": r"\b(?:discount|sale|special offer)\b|\d+\s*%\s*off\b"}[kind]
        if not re.search(required_word, kind_evidence, re.I):
            # A historical candidate label cannot make an ordinary current
            # price into a discount, bonus, or trial.
            continue
        price = f"{raw_price} {currency}"
        terms = description + " | Eligibility: " + eligibility
        result = dict(item)
        result.update(id=item.get("id") or "promo-" + hashlib.sha256(url.encode()).hexdigest()[:16],
                      name=name, url=final, official_domain=final_host.removeprefix("www."),
                      status="approved", reason="Rasmiy faol Offer: narx, shart va aniq muddatlar qayta tekshirildi",
                      type=kind, description=description, price=price, terms=terms,
                      starts_at=starts_at, expires_at=expires_at, verified_at=now.isoformat(),
                      checked_at=now.isoformat(), evidence={"url": final, "price": price,
                      "terms": terms, "starts_at": starts_at, "expires_at": expires_at})
        return result
    return _fail(item, "pending", "Rasmiy manbada nom, narx, shart va vaqt zonali aktiv muddatlarning to‘liq dalili yo‘q", now)
