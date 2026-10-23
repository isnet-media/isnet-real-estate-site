"""Exercise the production retry shell block against a concurrent local Git writer.

Uses temporary local repositories and stub collectors. Never contacts public
sites, GitHub remotes, or a production event feed.
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
WORKFLOW = ROOT / ".github/workflows/refresh-ashdod-event-images.yml"


def run(*args, cwd=None, env=None, check=True):
    return subprocess.run(
        list(args), cwd=cwd, env=env, text=True, capture_output=True, check=check
    )


def git(where, *args, check=True):
    return run("git", *args, cwd=where, check=check)


def configure(where):
    git(where, "config", "user.name", "image-safety-test")
    git(where, "config", "user.email", "image-safety-test@example.invalid")


def source_event(event_id, image=""):
    return {"event_id": event_id, "title": "Show " + event_id, "image": image}


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def event_file(where):
    return where / "events-preview/ashdod/data/events.json"


def report_file(where):
    return where / "events-preview/ashdod/data/image-enrichment-report.json"


def commit_step():
    text = WORKFLOW.read_text(encoding="utf-8")
    match = re.search(
        r"(?ms)^      - name: Commit image enrichment safely against concurrent writers\n"
        r"        run: \|\n((?:(?!^      - name:).|\n)*)",
        text,
    )
    if not match:
        raise AssertionError("Could not locate the actual safe image commit shell step")
    return textwrap.dedent(match.group(1)).strip() + "\n"


def fixture(corrupt=False):
    # The fake image collector edits the image only. An opt-in corrupt variant
    # removes an ID, to verify the real guard refuses to push that result.
    script = """import json, os
from pathlib import Path
p = Path('events-preview/ashdod/data/events.json')
data = json.loads(p.read_text(encoding='utf-8'))
for e in data['events']:
    e['image'] = 'verified-photo:' + e['event_id']
if os.environ.get('IMAGE_TEST_CORRUPT') == 'yes':
    data['events'].pop()
p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\\n', encoding='utf-8')
Path('events-preview/ashdod/data/image-enrichment-report.json').write_text('{"checked": true}\\n', encoding='utf-8')
"""
    return script


class ImageRetryIntegrationTest(unittest.TestCase):
    def test_concurrent_writer_is_preserved_on_retry(self):
        self.exercise(corrupt=False)

    def test_corrupt_recompute_is_rejected_without_publishing(self):
        self.exercise(corrupt=True)

    def exercise(self, corrupt):
        with tempfile.TemporaryDirectory(prefix="isnet-image-retry-") as tmp:
            root = Path(tmp)
            remote = root / "origin.git"
            seed = root / "seed"
            worker = root / "worker"
            other = root / "other"
            run("git", "init", "--bare", "-b", "main", str(remote))
            run("git", "init", "-b", "main", str(seed))
            configure(seed)

            write_json(event_file(seed), {"events": [source_event("alpha"), source_event("beta")]})
            write_json(report_file(seed), {"checked": False})
            scripts = seed / "scripts"
            scripts.mkdir()
            (scripts / "enrich_event_images_v3.py").write_text(fixture(), encoding="utf-8")
            (scripts / "clean_event_image_placeholders_v2.py").write_text("pass\n", encoding="utf-8")
            (scripts / "recover_event_listing_images.py").write_text("pass\n", encoding="utf-8")
            git(seed, "add", ".")
            git(seed, "commit", "-m", "seed")
            git(seed, "remote", "add", "origin", str(remote))
            git(seed, "push", "-u", "origin", "main")
            run("git", "clone", "--branch", "main", str(remote), str(worker))
            run("git", "clone", "--branch", "main", str(remote), str(other))
            configure(other)

            # The worker started image enrichment on a two-event snapshot.
            snapshot = root / "before.json"
            snapshot.write_text(event_file(worker).read_text(encoding="utf-8"), encoding="utf-8")
            worker_data = json.loads(event_file(worker).read_text(encoding="utf-8"))
            worker_data["events"][0]["image"] = "initial-image"
            write_json(event_file(worker), worker_data)
            write_json(report_file(worker), {"checked": True})

            # The other writer adds a distinct event while image refresh runs.
            fresh_data = json.loads(event_file(other).read_text(encoding="utf-8"))
            fresh_data["events"].append(source_event("gamma"))
            write_json(event_file(other), fresh_data)
            git(other, "add", ".")
            git(other, "commit", "-m", "concurrent event import")
            git(other, "push", "origin", "main")

            command = commit_step().replace("/tmp/ashdod-images-before.json", str(snapshot))
            env = os.environ.copy()
            if corrupt:
                env["IMAGE_TEST_CORRUPT"] = "yes"
            result = run("bash", "-e", "-c", command, cwd=worker, env=env, check=False)
            remote_text = git(root, "--git-dir=" + str(remote), "show",
                              "main:events-preview/ashdod/data/events.json").stdout
            published = json.loads(remote_text)["events"]
            self.assertEqual([e["event_id"] for e in published], ["alpha", "beta", "gamma"])
            if corrupt:
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertTrue(all(not e["image"] for e in published))
                self.assertIn("Safety stop", result.stderr)
            else:
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(all(e["image"].startswith("verified-photo:") for e in published))


if __name__ == "__main__":
    unittest.main()
