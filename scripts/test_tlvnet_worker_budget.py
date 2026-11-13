"""Regression tests for bounded TLVNET AI runner. No provider or CMS calls."""
import importlib.util
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

WORKER = Path(__file__).with_name("tlvnet_agent_worker.py")
spec = importlib.util.spec_from_file_location("tlvnet_agent_worker", WORKER)
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


class FakeRead:
    ok = True
    status_code = 200
    def __init__(self, rows):
        self.rows = rows
    def json(self):
        return self.rows


class FakeSession:
    def __init__(self):
        self.params = []
    def get(self, endpoint, params, timeout):
        self.params.append(params)
        return FakeRead([])


class WorkerBudgetTests(unittest.TestCase):
    def test_no_jobs_means_no_ai_calls_and_limit_two(self):
        session = FakeSession()
        with patch.object(worker, "make_session", return_value=session), \
             patch.dict(os.environ, {"SUPABASE_URL": "https://example.test", "SUPABASE_SERVICE_ROLE_KEY": "x", "OPENAI_API_KEY": "x"}, clear=False), \
             patch.object(worker.requests, "post", side_effect=AssertionError("unexpected paid API call")):
            self.assertEqual(worker.main(), 0)
        self.assertEqual(session.params[0]["limit"], "2")

    def test_job_limit_is_clamped(self):
        for configured, expected in [("0", "1"), ("99", "3")]:
            session = FakeSession()
            with patch.object(worker, "make_session", return_value=session), \
                 patch.dict(os.environ, {"SUPABASE_URL": "https://example.test", "SUPABASE_SERVICE_ROLE_KEY": "x", "OPENAI_API_KEY": "x", "TLVNET_MAX_JOBS_PER_RUN": configured}, clear=False):
                self.assertEqual(worker.main(), 0)
            self.assertEqual(session.params[0]["limit"], expected)

    def test_legacy_watch_flag_does_not_sleep_or_poll(self):
        env = os.environ.copy()
        env.pop("OPENAI_API_KEY", None)
        env.pop("SUPABASE_URL", None)
        env.pop("SUPABASE_SERVICE_ROLE_KEY", None)
        completed = subprocess.run([sys.executable, str(WORKER), "--watch-seconds", "180"], env=env, capture_output=True, text=True, timeout=8)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("single bounded sweep", completed.stdout)


if __name__ == "__main__":
    unittest.main()
