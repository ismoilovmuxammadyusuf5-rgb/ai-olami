"""Offline regression tests: discovery evidence, identity, and fail-closed offers."""
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from scripts.catalog import canonical_url, classify_ai, merge_candidates, parse_feed
from scripts.promotions import verify_promotion
from scripts.update_catalog import run_update
from scripts.network import validate_target


NOW = datetime(2026, 11, 24, tzinfo=timezone.utc)
STAMP = NOW.isoformat()


def ai_item(**changes):
    result = {
        "name": "SketchBot",
        "url": "https://www.producthunt.com/products/sketchbot/",
        "description": "An AI image generator that creates illustrations from text prompts.",
        "source": "Product Hunt",
        "source_url": "https://www.producthunt.com/feed",
        "categories": ["Artificial Intelligence"],
    }
    result.update(changes)
    return result


class FeedTests(unittest.TestCase):
    def test_rss_decodes_html_and_retains_source(self):
        feed = b'''<rss version="2.0"><channel><item>
          <title>SketchBot</title><link>https://example.com/sketch</link>
          <description>&lt;p&gt;AI image generator &amp;amp; editor&lt;/p&gt;</description>
          <category>Artificial Intelligence</category><pubDate>Mon, 23 Nov 2026 10:00:00 GMT</pubDate>
        </item></channel></rss>'''
        rows = parse_feed(feed, "Product Hunt", "https://www.producthunt.com/feed")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["name"], "SketchBot")
        self.assertNotIn("<p>", rows[0]["description"])
        self.assertIn("generator", rows[0]["description"])
        self.assertEqual(rows[0]["source"], "Product Hunt")
        self.assertIn("Artificial Intelligence", rows[0]["categories"])

    def test_atom_uses_alternate_article_not_self_link(self):
        feed = b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry>
          <title>Agent Code</title><link rel="self" href="https://example.com/feed/1"/>
          <link rel="alternate" href="https://example.com/agent"/>
          <summary>AI coding assistant that writes code.</summary>
          <category term="Artificial Intelligence"/><updated>2026-11-23T10:00:00Z</updated>
        </entry></feed>'''
        rows = parse_feed(feed, "Example", "https://example.com/feed")
        self.assertEqual(rows[0]["url"], "https://example.com/agent")
        self.assertIn("Artificial Intelligence", rows[0]["categories"])

    def test_malformed_xml_does_not_return_fake_candidates(self):
        with self.assertRaises(Exception):
            parse_feed(b"<rss><channel>broken", "Example", "https://example.com/rss")

    def test_missing_title_or_url_is_ignored(self):
        feed = b'''<rss><channel><item><title>No link</title></item>
          <item><link>https://example.com/no-name</link></item></channel></rss>'''
        self.assertEqual(parse_feed(feed, "Example", "https://example.com/rss"), [])


class IdentityTests(unittest.TestCase):
    def test_tracking_www_fragment_and_slash_deduplicate(self):
        a = canonical_url("https://www.Example.com/tool/?utm_source=ph&ref=launch#features")
        b = canonical_url("https://example.com/tool")
        self.assertEqual(a, b)

    def test_meaningful_query_is_not_silently_removed(self):
        self.assertNotEqual(canonical_url("https://example.com/tool?id=1"),
                            canonical_url("https://example.com/tool?id=2"))

    def test_non_web_and_private_targets_are_invalid(self):
        for url in ("javascript:alert(1)", "http://example.com", "https://127.0.0.1/a",
                    "https://localhost/a", "https://user:pass@example.com/", "https://10.0.0.1/"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                canonical_url(url)

    def test_same_url_refreshes_legacy_record_without_duplicate(self):
        old = [{"name": "SketchBot", "url": "https://producthunt.com/products/sketchbot",
                "source": "Product Hunt", "status": "pending"}]
        rows = merge_candidates(old, [ai_item()], STAMP)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "approved")
        self.assertTrue(rows[0].get("evidence"))

    def test_stable_id_and_approval_date_on_repeat(self):
        first = merge_candidates([], [ai_item()], STAMP)
        second = merge_candidates(first, [ai_item()], "2026-11-25T00:00:00+00:00")
        self.assertEqual(len(second), 1)
        self.assertEqual(first[0]["id"], second[0]["id"])
        self.assertEqual(first[0]["approved_at"], second[0]["approved_at"])

    def test_previously_verified_tools_survive_source_outage(self):
        first = merge_candidates([], [ai_item()], STAMP)
        result = merge_candidates(first, [], "2026-11-25T00:00:00+00:00")
        self.assertEqual(result[0]["status"], "approved")
        self.assertEqual(result[0]["id"], first[0]["id"])

    def test_legacy_names_are_not_invented_into_ai_evidence(self):
        rows = merge_candidates([{"name": "Unknown", "url": "https://example.com/unknown",
                                  "status": "pending", "source": "Product Hunt"}], [], STAMP)
        self.assertEqual(rows[0]["status"], "pending")

    def test_unsupported_approved_flag_is_not_evidence(self):
        rows = merge_candidates([{"name": "Unknown", "url": "https://example.com/unknown",
                                  "status": "approved", "source": "Product Hunt"}], [], STAMP)
        self.assertNotEqual(rows[0]["status"], "approved")


class ClassificationTests(unittest.TestCase):
    def test_functional_ai_tool_approved_in_matching_category(self):
        status, reason, category = classify_ai(ai_item())
        self.assertEqual(status, "approved")
        self.assertEqual(category, "Rasm va San’at")
        self.assertTrue(reason)

    def test_ai_compatible_is_not_ai_tool(self):
        status, _, _ = classify_ai(ai_item(name="DeskStand", description="An AI-compatible laptop stand for your office.", categories=[]))
        self.assertNotEqual(status, "approved")

    def test_category_only_ai_tag_is_not_sufficient(self):
        status, _, _ = classify_ai(ai_item(name="Calendar", description="Share calendars with your team."))
        self.assertNotEqual(status, "approved")

    def test_clear_non_ai_product_rejected(self):
        status, _, _ = classify_ai(ai_item(name="Bottle", description="A stainless steel water bottle.", categories=[]))
        self.assertEqual(status, "rejected")

    def test_missing_description_pending(self):
        status, _, _ = classify_ai(ai_item(name="NewAI", description="", categories=[]))
        self.assertEqual(status, "pending")

    def test_news_is_not_catalog_product(self):
        status, _, _ = classify_ai(ai_item(name="Our latest AI safety research", description="We announce a report on how AI can affect society.", source="OpenAI"))
        self.assertNotEqual(status, "approved")

    def test_newsletter_covering_ai_research_is_not_ai_tool(self):
        status, _, _ = classify_ai(ai_item(name="AI Daily", description="A newsletter covering AI research and helping you discover the latest tools."))
        self.assertNotEqual(status, "approved")

    def test_ai_course_teaching_code_is_not_ai_tool(self):
        status, _, _ = classify_ai(ai_item(name="AI Academy", description="An AI course teaching developers how to write code and build applications."))
        self.assertNotEqual(status, "approved")

    def test_directory_search_is_not_itself_ai_function(self):
        status, _, _ = classify_ai(ai_item(name="AI Tools Library", description="A directory of AI tools. Search and find software for your projects."))
        self.assertNotEqual(status, "approved")

    def test_collection_of_ai_logos_is_not_ai_tool(self):
        status, _, _ = classify_ai(ai_item(name="AI Brand Kit", description="A collection of AI company logos to help you design presentations."))
        self.assertNotEqual(status, "approved")

    def test_product_for_ai_teams_does_not_imply_ai_function(self):
        status, _, _ = classify_ai(ai_item(name="TeamDesk", description="Designed for AI teams. Share files and manage tasks."))
        self.assertNotEqual(status, "approved")


class NetworkBoundaryTests(unittest.TestCase):
    def test_dns_to_private_address_is_blocked(self):
        with patch("scripts.network.socket.getaddrinfo", return_value=[(2, 1, 6, "", ("192.168.1.2", 443))]):
            with self.assertRaises(ValueError):
                validate_target("https://feed.example.com/rss", {"feed.example.com"})

    def test_host_allowlist_requires_exact_domain(self):
        with self.assertRaises(ValueError):
            validate_target("https://blog.google.attacker.com/rss", {"blog.google"})

    def test_mixed_public_and_private_dns_is_blocked(self):
        answers = [(2, 1, 6, "", ("8.8.8.8", 443)), (2, 1, 6, "", ("10.0.0.1", 443))]
        with patch("scripts.network.socket.getaddrinfo", return_value=answers):
            with self.assertRaises(ValueError):
                validate_target("https://feed.example.com/rss", {"feed.example.com"})


class PromotionTests(unittest.TestCase):
    def setUp(self):
        self.item = {
            "name": "Gemini AI trial", "source": "Google", "type": "trial",
            "url": "https://blog.google/products/gemini-trial", "status": "pending",
        }
        self.offer = {
            "@context": "https://schema.org", "@type": "Offer", "name": "Gemini AI trial",
            "price": "0", "priceCurrency": "USD",
            "description": "New individual users only; one month trial; payment method required",
            "validFrom": "2026-11-01T00:00:00Z", "priceValidUntil": "2026-12-01T00:00:00Z",
            "availability": "https://schema.org/InStock",
            "eligibleCustomerType": "New individual users",
        }

    def fetcher(self, offer=None, final_url=None):
        document = json.dumps(self.offer if offer is None else offer)
        def fetch(url, allowed_hosts=None):
            return (f'<html><script type="application/ld+json">{document}</script></html>'.encode(),
                    final_url or url)
        return fetch

    def verify(self, offer=None, **item_changes):
        item = dict(self.item, **item_changes)
        return verify_promotion(item, self.fetcher(offer), NOW)

    def test_complete_official_active_offer_is_approved_with_exact_evidence(self):
        result = self.verify()
        self.assertEqual(result["status"], "approved")
        self.assertIn("USD", str(result["price"]))
        self.assertTrue(result["terms"])
        for field in ("url", "price", "terms", "starts_at", "expires_at"):
            self.assertTrue(result["evidence"].get(field), field)
        self.assertTrue(result.get("verified_at"))

    def test_missing_end_never_approved(self):
        offer = dict(self.offer)
        offer.pop("priceValidUntil")
        self.assertEqual(self.verify(offer)["status"], "pending")

    def test_date_only_and_timezone_free_end_never_approved(self):
        for end in ("2026-12-01", "2026-12-01T23:59:59"):
            with self.subTest(end=end):
                self.assertEqual(self.verify(dict(self.offer, priceValidUntil=end))["status"], "pending")

    def test_expired_offer_is_expired(self):
        self.assertEqual(self.verify(dict(self.offer, priceValidUntil="2026-11-23T23:59:59Z"))["status"], "expired")

    def test_future_offer_not_yet_active(self):
        self.assertEqual(self.verify(dict(self.offer, validFrom="2026-11-25T00:00:00Z"))["status"], "pending")

    def test_missing_price_terms_or_eligibility_is_not_approved(self):
        for field in ("price", "priceCurrency", "description", "eligibleCustomerType", "validFrom", "availability"):
            with self.subTest(field=field):
                offer = dict(self.offer)
                offer.pop(field)
                self.assertNotEqual(self.verify(offer)["status"], "approved")

    def test_numeric_or_boolean_values_are_not_human_terms(self):
        for field, value in (("description", 1), ("description", True), ("eligibleCustomerType", True)):
            with self.subTest(field=field, value=value):
                self.assertNotEqual(self.verify(dict(self.offer, **{field: value}))["status"], "approved")

    def test_truncated_conditions_do_not_count_as_complete_proof(self):
        offer = dict(self.offer, description="trial terms " * 250 + " Restriction at end: no new enrollments.")
        self.assertNotEqual(self.verify(offer)["status"], "approved")

    def test_conflicting_expiry_fields_do_not_approve_past_validity(self):
        for extra in ({"validThrough": "2026-11-22T00:00:00Z"},
                      {"availabilityEnds": "2026-11-22T00:00:00Z"},
                      {"validThrough": "2026-11-30T00:00:00Z"}):
            with self.subTest(extra=extra):
                self.assertNotEqual(self.verify(dict(self.offer, **extra))["status"], "approved")

    def test_wrong_named_offer_is_not_evidence(self):
        result = self.verify(dict(self.offer, name="Unrelated conference ticket"))
        self.assertNotEqual(result["status"], "approved")

    def test_manipulated_or_unofficial_urls_are_rejected(self):
        for url in ("https://blog.google.evil.com/trial", "https://evil.com/trial",
                    "https://blog.google@evil.com/trial", "https://blog.google/trial?redirect=https://evil.com"):
            with self.subTest(url=url):
                result = verify_promotion(dict(self.item, url=url), self.fetcher(final_url="https://evil.com/trial"), NOW)
                self.assertNotEqual(result["status"], "approved")

    def test_official_url_redirecting_outside_allowlist_is_not_approved(self):
        result = verify_promotion(self.item, self.fetcher(final_url="https://external.example/trial"), NOW)
        self.assertNotEqual(result["status"], "approved")

    def test_previous_approval_removed_on_fetch_failure(self):
        previous = self.verify()
        def fail(url, allowed_hosts=None):
            raise OSError("source unavailable")
        result = verify_promotion(previous, fail, NOW)
        self.assertEqual(result["status"], "pending")

    def test_old_evidence_does_not_override_changed_terms(self):
        previous = self.verify()
        changed = dict(self.offer, price="7", description="Existing subscribers only; auto renews at USD 7",
                       eligibleCustomerType="Existing subscribers")
        result = verify_promotion(previous, self.fetcher(changed), NOW)
        self.assertEqual(result["status"], "approved")
        self.assertIn("7", str(result["price"]))
        self.assertIn("Existing", result["terms"])

    def test_unstructured_price_and_date_prose_not_guessed(self):
        def prose(url, allowed_hosts=None):
            return b"<p>Free until next month. Use code TRYAI. Terms apply.</p>", url
        self.assertEqual(verify_promotion(self.item, prose, NOW)["status"], "pending")

    def test_removed_availability_never_approved(self):
        self.assertNotEqual(self.verify(dict(self.offer, availability="https://schema.org/OutOfStock"))["status"], "approved")


class UpdateTests(unittest.TestCase):
    SOURCES = [
        {"name": "Product Hunt", "url": "https://www.producthunt.com/feed",
         "hosts": ["www.producthunt.com", "producthunt.com"], "kind": "discovery"},
        {"name": "OpenAI", "url": "https://openai.com/news/rss.xml",
         "hosts": ["openai.com", "www.openai.com"], "kind": "official"},
    ]
    FEED = b'''<rss><channel><item><title>SketchBot</title>
        <link>https://www.producthunt.com/products/sketchbot</link>
        <description>An AI image generator that creates illustrations from text prompts.</description>
        </item></channel></rss>'''

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def read(self, filename):
        return json.loads((self.folder / filename).read_text(encoding="utf-8"))

    def success(self, url, allowed_hosts=None):
        return self.FEED, url

    def test_partial_feed_failure_keeps_successful_discoveries(self):
        def partial(url, allowed_hosts=None):
            if "openai.com" in url:
                raise OSError("feed unavailable")
            return self.FEED, url
        result = run_update(self.folder, fetcher=partial, now=NOW, sources=self.SOURCES)
        self.assertEqual(result["overall_status"], "partial")
        self.assertEqual({row["status"] for row in result["sources"]}, {"ok", "error"})
        self.assertTrue(self.read("approved-ai.json")["tools"])
        self.assertEqual(self.read("ai-candidates.json")["candidates"][0]["status"], "approved")

    def test_total_outage_retains_catalog_and_last_success(self):
        initial = run_update(self.folder, fetcher=self.success, now=NOW, sources=self.SOURCES)
        before = self.read("approved-ai.json")["tools"]
        def outage(url, allowed_hosts=None):
            raise OSError("all unavailable")
        later = datetime(2026, 11, 25, tzinfo=timezone.utc)
        result = run_update(self.folder, fetcher=outage, now=later, sources=self.SOURCES)
        self.assertEqual(result["overall_status"], "error")
        self.assertEqual(result["last_success_at"], initial["last_success_at"])
        self.assertEqual(self.read("approved-ai.json")["tools"], before)
        self.assertTrue(all(row["status"] == "error" for row in result["sources"]))

    def test_malformed_source_isolated_from_other_source(self):
        def malformed(url, allowed_hosts=None):
            return (b"<rss>broken" if "openai.com" in url else self.FEED), url
        result = run_update(self.folder, fetcher=malformed, now=NOW, sources=self.SOURCES)
        self.assertEqual(result["overall_status"], "partial")
        self.assertTrue(self.read("approved-ai.json")["tools"])
        self.assertTrue(next(s for s in result["sources"] if s["name"] == "OpenAI").get("error"))

    def test_corrupt_data_does_not_silently_overwrite_existing_file(self):
        path = self.folder / "ai-candidates.json"
        original = "{broken-json"
        path.write_text(original, encoding="utf-8")
        with self.assertRaises(Exception):
            run_update(self.folder, fetcher=self.success, now=NOW, sources=self.SOURCES)
        self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_official_pending_page_budget_rotates_across_runs(self):
        offers = [{"name": "Gemini AI trial", "source": "Google", "status": "pending",
                   "url": f"https://blog.google/products/trial-{i}", "found_at": STAMP}
                  for i in range(13)]
        (self.folder / "promo-candidates.json").write_text(json.dumps({"promotions": offers}), encoding="utf-8")
        fetched = []
        def page(url, allowed_hosts=None):
            fetched.append(url)
            return b"<html><p>Details unavailable.</p></html>", url
        run_update(self.folder, fetcher=page, now=NOW, sources=[])
        first = set(fetched)
        self.assertEqual(len(first), 12)
        unseen = set(row["url"] for row in offers) - first
        fetched.clear()
        run_update(self.folder, fetcher=page, now=datetime(2026, 11, 24, 1, tzinfo=timezone.utc), sources=[])
        self.assertTrue(unseen.issubset(set(fetched)))

    def test_unofficial_leads_do_not_consume_official_page_budget(self):
        leads = [{"name": f"AI promo {i}", "source": "Product Hunt", "status": "pending",
                  "url": f"https://producthunt.com/products/promo-{i}", "found_at": STAMP}
                 for i in range(15)]
        leads.append({"name": "Gemini AI trial", "source": "Google", "status": "pending",
                      "url": "https://blog.google/products/trial", "found_at": STAMP})
        (self.folder / "promo-candidates.json").write_text(json.dumps({"promotions": leads}), encoding="utf-8")
        fetched = []
        def page(url, allowed_hosts=None):
            fetched.append(url)
            return b"<html>Details unavailable.</html>", url
        run_update(self.folder, fetcher=page, now=NOW, sources=[])
        self.assertIn("https://blog.google/products/trial", fetched)
        self.assertFalse(any("producthunt.com" in url for url in fetched))


if __name__ == "__main__":
    unittest.main()
