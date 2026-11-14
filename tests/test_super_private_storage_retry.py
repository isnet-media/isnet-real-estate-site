"""No-network regression tests for fail-closed, create-only private Storage writes."""
import io
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from scripts import stage_super_private_storage as storage


def http_error(code):
    return HTTPError("https://example.invalid/immutable", code, "test", {},
                     io.BytesIO(b'backend returned an error'))


class ImmutablePrivateRetryTests(unittest.TestCase):
    def upload(self, verified):
        return storage.upload_immutable_verified(
            "https://example.invalid/immutable", "dummy-secret", b"data",
            "application/json", "SUPER.RISHON/data/offers/81.json", verified)

    @patch.object(storage.time, "sleep")
    @patch.object(storage, "call")
    def test_http_520_then_retry_only_after_missing_sha_readback(self, request, sleep):
        request.side_effect = [http_error(520), (201, b"")]
        verified = Mock(side_effect=[False, False, True])
        self.upload(verified)
        self.assertEqual(request.call_count, 2)
        self.assertEqual(verified.call_count, 3)
        sleep.assert_called_once_with(1)

    @patch.object(storage.time, "sleep")
    @patch.object(storage, "call")
    def test_ambiguous_520_with_matching_object_never_reposts(self, request, sleep):
        request.side_effect = [http_error(520)]
        self.upload(Mock(side_effect=[False, True]))
        request.assert_called_once()
        sleep.assert_not_called()

    @patch.object(storage.time, "sleep")
    @patch.object(storage, "call")
    def test_conflict_can_only_pass_with_authenticated_matching_read(self, request, sleep):
        request.side_effect = [http_error(409)]
        self.upload(Mock(side_effect=[False, True]))
        request.assert_called_once()
        sleep.assert_not_called()

    @patch.object(storage.time, "sleep")
    @patch.object(storage, "call")
    def test_permission_failure_is_never_retried(self, request, sleep):
        request.side_effect = [http_error(403)]
        with self.assertRaisesRegex(RuntimeError, "HTTP 403"):
            self.upload(Mock(return_value=False))
        request.assert_called_once()
        sleep.assert_not_called()

    @patch.object(storage.time, "sleep")
    @patch.object(storage, "call")
    def test_transient_retry_budget_exhaustion_aborts(self, request, sleep):
        request.side_effect = [http_error(520)] * 4
        with self.assertRaisesRegex(RuntimeError, "HTTP 520"):
            self.upload(Mock(return_value=False))
        self.assertEqual(request.call_count, 4)
        self.assertEqual(sleep.call_count, 3)

    @patch.object(storage, "call")
    def test_existing_sha_mismatch_stops_before_any_post(self, request):
        with self.assertRaisesRegex(RuntimeError, "Immutable object mismatch"):
            self.upload(Mock(side_effect=RuntimeError("Immutable object mismatch")))
        request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
