"""Offline invariants for the attributed bulk catalogue."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import sync_catalog as sync


def record(name="Useful AI", website="https://useful.ai/", **changes):
    row = {"name": name, "website": website, "category": "coding", "description": "AI coding assistant."}
    row.update(changes)
    return row


class NormalizationTests(unittest.TestCase):
    def test_source_free_trial_is_not_a_free_plan(self):
        row = sync.normalize(record(pricingModel="Free Trial"), "AGIPicks")
        self.assertEqual(row["pricing_model"], ["Free Trial"])
        self.assertIsNone(row["free_plan"])
        row = sync.normalize(record(pricingModel="freemium", freePlan=True), "AGIPicks")
        self.assertTrue(row["free_plan"])
        self.assertEqual(row["pricing_model"], ["freemium"])

    def test_no_invented_dates_prices_or_description(self):
        row = sync.normalize(record(description="", pricingModel="Free", verifiedAt="2026-02-30"), "AIToolBuzz")
        self.assertEqual(row["short_description"], "")
        self.assertEqual(row["source_date"], "")
        self.assertEqual(row["last_verified"], "")
        self.assertEqual(row["pricing_model"], [])
        self.assertIsNone(row["free_plan"])

    def test_source_verification_and_attribution_are_preserved(self):
        row = sync.normalize(record(verifiedAt="2026-11-20"), "AGIPicks")
        self.assertEqual(row["last_verified"], "2026-11-20")
        self.assertEqual(row["source_url"], "https://agipicks.com/data/")
        self.assertEqual(row["license"], "CC-BY-4.0")

    def test_tior_schema_and_false_open_source(self):
        row = sync.normalize({"name": "Image AI", "official_url": "https://image.ai/", "short_description": "Image tool", "primary_category": "Image generation and editing", "pricing_model": ["Paid", "Free Trial"], "open_source": False, "last_verified": "2026-08-18"}, "TiorAI")
        self.assertEqual(row["primary_category"], "Rasm va San’at")
        self.assertEqual(row["pricing_model"], ["Paid", "Free Trial"])
        self.assertFalse(row["open_source"])
        self.assertEqual(row["source_date"], "2026-08-18")

    def test_unsafe_urls_and_retired_records_are_rejected(self):
        for url in ("javascript:alert(1)", "https://127.0.0.1/", "https://user:pass@tool.ai/", "https://tool.local/", "https://localhost/", "https://tool.ai:8443/", "https://example.com/"):
            self.assertIsNone(sync.normalize(record(website=url), "AGIPicks"), url)
        self.assertIsNone(sync.normalize(record(retired={"reason": "closed"}), "AGIPicks"))
        self.assertIsNone(sync.normalize(record(status="Error 404"), "AIToolBuzz"))

    def test_names_and_tracking_www_slashes_are_deduplicated(self):
        a = sync.normalize(record("Tool.AI", "https://www.tool.ai/?utm_source=news&ref=directory#x"), "AGIPicks")
        b = sync.normalize(record("Another name", "https://tool.ai"), "TiorAI")
        c = sync.normalize(record("ＴＯＯＬ-ai", "https://other.ai/"), "TiorAI")
        self.assertEqual(len(sync.dedupe([a, b, c])), 1)
        self.assertNotEqual(sync.canonical_url("https://tool.ai/?id=1"), sync.canonical_url("https://tool.ai/?id=2"))

    def test_source_payload_cannot_be_an_error_document(self):
        for payload in (b'{"error":"upstream unavailable"}', b'[]', b'["not a record"]'):
            with self.assertRaises(ValueError):
                sync.parse_source(payload, "AGIPicks")

    def test_csv_uses_official_website_and_strips_markup(self):
        rows = sync.parse_source(b'Name,Website,Short Description,Category,Website Status\r\n"Real Tool",https://realtool.ai/,"<b>AI</b> image editor",Art,Active\r\n', "AIToolBuzz")
        self.assertEqual(rows[0]["short_description"], "AI image editor")
        self.assertEqual(rows[0]["official_url"], "https://realtool.ai/")


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "catalogue.json"
        self.stamp = "2026-11-24T00:00:00+00:00"

    def response(self, count):
        return json.dumps({"tools": [record(f"Product {i}", f"https://product{i}.ai/") for i in range(count)]}).encode()

    def test_initial_insufficient_catalogue_is_not_written(self):
        with self.assertRaises(ValueError):
            sync.sync(self.path, lambda url: self.response(1), self.stamp)
        self.assertFalse(self.path.exists())

    def test_source_outage_preserves_previous_cache_byte_for_byte(self):
        with patch.object(sync, "MIN_TOOLS", 2):
            sync.sync(self.path, lambda url: self.response(3) if "agipicks.com" in url else b'[]', self.stamp)
            before = self.path.read_bytes()
            def unavailable(url):
                raise TimeoutError("offline")
            result = sync.sync(self.path, unavailable, "2026-11-25T00:00:00+00:00")
            self.assertTrue(result["retained"])
            self.assertEqual(before, self.path.read_bytes())

    def test_large_drop_retains_previous_cache(self):
        with patch.object(sync, "MIN_TOOLS", 2):
            sync.sync(self.path, lambda url: self.response(10) if "agipicks.com" in url else b'[]', self.stamp)
            before = self.path.read_bytes()
            sync.sync(self.path, lambda url: self.response(8) if "agipicks.com" in url else b'[]', self.stamp)
            self.assertEqual(before, self.path.read_bytes())

    def test_first_seen_is_retained_and_counter_matches_actual_rows(self):
        with patch.object(sync, "MIN_TOOLS", 2):
            sync.sync(self.path, lambda url: self.response(3) if "agipicks.com" in url else b'[]', self.stamp)
            sync.sync(self.path, lambda url: self.response(4) if "agipicks.com" in url else b'[]', "2026-11-25T00:00:00+00:00")
            doc = json.loads(self.path.read_text())
            self.assertEqual(sum(doc["sources"].values()), len(doc["tools"]))
            self.assertEqual(doc["tools"][0]["first_seen_at"], self.stamp)
            self.assertEqual(doc["tools"][-1]["first_seen_at"], "2026-11-25T00:00:00+00:00")

    def test_tampered_counter_or_provenance_blocks_publication(self):
        with patch.object(sync, "MIN_TOOLS", 2):
            sync.sync(self.path, lambda url: self.response(3) if "agipicks.com" in url else b'[]', self.stamp)
            document = json.loads(self.path.read_text())
            document["sources"]["AGIPicks"] = 1500
            with self.assertRaises(ValueError):
                sync.validate_document(document)
            document["sources"]["AGIPicks"] = 3
            document["tools"][0]["source_url"] = "https://untrusted.ai/"
            with self.assertRaises(ValueError):
                sync.validate_document(document)


if __name__ == "__main__":
    unittest.main()
