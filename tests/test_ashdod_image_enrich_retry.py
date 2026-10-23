"""Integration tests for real Ashdod image-enrichment retry shell code.

The test uses an isolated local Git remote and fake image collectors.
It never calls public event sources, GitHub, or a production database.
"""
import json
import os
import re
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/enrich-events-images.yml"


def command(*args, cwd=None, env=None, check=True):
    return subprocess.run(list(args), cwd=cwd, env=env, text=True,
                          capture_output=True, check=check)


def git(where, *args):
    return command("git", *args, cwd=where)


def configure(where):
    git(where, "config", "user.name", "image-enrich-safety-test")
    git(where, "config", "user.email", "image-enrich-safety-test@example.invalid")


def event_file(where):
    return where / "events-preview/ashdod/data/events.json"


def report_file(where):
    return where / "events-preview/ashdod/data/image-enrichment-report.json"


def listing_file(where):
    return where / "events-preview/ashdod/data/listing-image-fill-report.json"


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def retry_shell():
    source = WORKFLOW.read_text(encoding="utf-8")
    match = re.search(
        r"(?ms)^      - name: Commit image-only enrichment with safe retry on concurrent updates\n"
        r"        run: \|\n((?:(?!^      - name:).|\n)*)",
        source,
    )
    if not match:
        raise AssertionError("The actual image-enrichment safe commit step was not found")
    return textwrap.dedent(match.group(1)).strip() + "\n"


class EnrichmentRetryTests(unittest.TestCase):
    def test_event_added_by_another_writer_is_preserved(self):
        self.exercise(corrupt=False)

    def test_corrupt_image_recompute_never_publishes(self):
        self.exercise(corrupt=True)

    def test_workflow_fails_instead_of_force_pushing(self):
        script = retry_shell()
        self.assertIn("git fetch origin main", script)
        self.assertIn("git reset --hard origin/main", script)
        self.assertIn("python scripts/enrich_event_images_v3.py", script)
        self.assertIn("git push origin HEAD:main", script)
        self.assertNotIn("git push --force", script)
        self.assertNotIn("git push -f", script)
        self.assertRegex(script, r"assert ids\(a\)==ids\(b\)")

    def exercise(self, corrupt):
        with tempfile.TemporaryDirectory(prefix="isnet-enrich-retry-") as temp:
            root = Path(temp)
            remote = root / "origin.git"
            seed = root / "seed"
            worker = root / "worker"
            other = root / "other"

            command("git", "init", "--bare", "-b", "main", str(remote))
            command("git", "init", "-b", "main", str(seed))
            configure(seed)
            write_json(event_file(seed), {"events": [
                {"event_id": "alpha", "image": ""},
                {"event_id": "beta", "image": ""},
            ]})
            write_json(report_file(seed), {"stage": "seed"})
            write_json(listing_file(seed), {"stage": "seed"})
            assets = seed / "events-preview/ashdod/assets/events"
            assets.mkdir(parents=True)
            (assets / ".keep").write_text("", encoding="utf-8")
            scripts = seed / "scripts"
            scripts.mkdir()
            collector = """import json, os
from pathlib import Path
p = Path('events-preview/ashdod/data/events.json')
obj = json.loads(p.read_text(encoding='utf-8'))
for e in obj['events']:
    e['image'] = 'photo:' + e['event_id']
if os.environ.get('IMAGE_TEST_CORRUPT') == 'yes':
    obj['events'].pop()
p.write_text(json.dumps(obj, indent=2) + '\\n', encoding='utf-8')
Path('events-preview/ashdod/data/image-enrichment-report.json').write_text('{"checked": true}\\n', encoding='utf-8')
"""
            (scripts / "enrich_event_images_v3.py").write_text(collector, encoding="utf-8")
            for script in ("fast_fill_event_images_from_listings.py",
                           "reuse_media_bank_images.py",
                           "clean_event_image_placeholders_v2.py"):
                (scripts / script).write_text("pass\n", encoding="utf-8")
            git(seed, "add", ".")
            git(seed, "commit", "-m", "seed")
            git(seed, "remote", "add", "origin", str(remote))
            git(seed, "push", "-u", "origin", "main")
            command("git", "clone", "--branch", "main", str(remote), str(worker))
            command("git", "clone", "--branch", "main", str(remote), str(other))
            configure(other)

            before = root / "before.json"
            before.write_text(event_file(worker).read_text(encoding="utf-8"), encoding="utf-8")

            # Old runner did some work, then another writer imported an event.
            events = json.loads(event_file(worker).read_text(encoding="utf-8"))
            events["events"][0]["image"] = "stale"
            write_json(event_file(worker), events)
            write_json(report_file(worker), {"stage": "stale"})

            updated = json.loads(event_file(other).read_text(encoding="utf-8"))
            updated["events"].append({"event_id": "gamma", "image": ""})
            write_json(event_file(other), updated)
            git(other, "add", ".")
            git(other, "commit", "-m", "import gamma")
            git(other, "push", "origin", "main")

            script = retry_shell().replace("/tmp/ashdod-images-before.json", str(before))
            env = os.environ.copy()
            if corrupt:
                env["IMAGE_TEST_CORRUPT"] = "yes"
            run = command("bash", "-e", "-c", script, cwd=worker, env=env, check=False)

            after = json.loads(git(root, "--git-dir=" + str(remote), "show",
                                   "main:events-preview/ashdod/data/events.json").stdout)["events"]
            self.assertEqual([e["event_id"] for e in after], ["alpha", "beta", "gamma"])
            if corrupt:
                self.assertNotEqual(run.returncode, 0, run.stdout)
                self.assertTrue(all(not e["image"] for e in after))
                self.assertIn("Safety stop", run.stderr)
            else:
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertTrue(all(e["image"] == "photo:" + e["event_id"] for e in after))


if __name__ == "__main__":
    unittest.main()
