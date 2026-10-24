"""Safety regression tests for permanent OpenAI API quota failures."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import enrich_event_content_ai as enrichment


class QuotaFailFastTests(unittest.TestCase):
    def test_explicit_billing_quota_error_is_not_a_transient_429(self):
        response = SimpleNamespace(
            ok=False,
            status_code=429,
            text='{"error":{"type":"insufficient_quota","code":"credit_balance_exhausted"}}',
        )
        with mock.patch.object(enrichment.requests, "post", return_value=response) as post:
            with self.assertRaises(enrichment.ApiQuotaExhausted):
                enrichment.ask_model({"title": "Testing", "category": "music"}, "Existing verified source description", "")
        self.assertEqual(post.call_count, 1)

    def test_stop_after_first_quota_response_without_writing_feed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            feed = root / "events.json"
            report = root / "content-enrichment-report.json"
            events = [
                {
                    "event_id": name,
                    "title": "Sample production",
                    "start_date": (date.today() + timedelta(days=1)).isoformat(),
                    "category": "music",
                    "source_detail_text": "Verified production description. " * 10,
                }
                for name in ("first", "second")
            ]
            feed.write_text(json.dumps({"events": events}, ensure_ascii=False), encoding="utf-8")
            before = feed.read_bytes()
            with (
                mock.patch.object(enrichment, "CITIES", {"ashdod": feed}),
                mock.patch.object(enrichment, "REPORT", report),
                mock.patch.object(enrichment, "TARGET_CITY", "ashdod"),
                mock.patch.object(enrichment, "API_KEY", "test-api-key"),
                mock.patch.object(enrichment, "MAX_EVENTS", 6),
                mock.patch.object(enrichment, "ask_model", side_effect=enrichment.ApiQuotaExhausted("credit_balance_exhausted")) as ask,
                mock.patch.object(enrichment.time, "sleep"),
            ):
                code = enrichment.main()
            self.assertEqual(code, 2)
            self.assertEqual(ask.call_count, 1)
            self.assertEqual(before, feed.read_bytes())
            diagnostic = json.loads(report.read_text(encoding="utf-8"))
            self.assertTrue(diagnostic["api_quota_exhausted"])
            self.assertEqual(diagnostic["model_failed"], 1)
            self.assertEqual(len(diagnostic["events"]), 1)

    def test_transient_api_error_is_still_retryable(self):
        response = SimpleNamespace(ok=False, status_code=429, text='{"error":{"code":"rate_limit_exceeded"}}')
        with mock.patch.object(enrichment.requests, "post", return_value=response):
            with self.assertRaises(RuntimeError) as raised:
                enrichment.ask_model({"title": "Testing", "category": "music"}, "Verified source", "")
        self.assertNotIsInstance(raised.exception, enrichment.ApiQuotaExhausted)


if __name__ == "__main__":
    unittest.main()
