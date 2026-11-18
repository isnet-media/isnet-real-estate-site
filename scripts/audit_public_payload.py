"""Read-only public asset inventory for deployment diagnostics.

Reports the heaviest top-level paths, without removing or altering assets.
This is deliberately distinct from GitHub repository size and server disk use.
"""
import argparse
import json
from pathlib import Path

def inventory(root):
    if not root.is_dir():
        raise ValueError("Public staging directory does not exist")
    totals = {}
    count = 0
    total = 0
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("Refusing symlink in public payload")
        if not path.is_file():
            continue
        size = path.stat().st_size
        count += 1
        total += size
        group = path.relative_to(root).parts[0]
        item = totals.setdefault(group, {"bytes": 0, "files": 0})
        item["bytes"] += size
        item["files"] += 1
    return {
        "total_bytes": total,
        "file_count": count,
        "top_level": [
            {"path": name, **entry}
            for name, entry in sorted(totals.items(), key=lambda x: -x[1]["bytes"])
        ],
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--github-summary", type=Path)
    args = parser.parse_args()
    report = inventory(args.root)
    print(json.dumps(report, ensure_ascii=False))
    if args.github_summary:
        lines = [
            "### Public deployment payload (not server disk usage)",
            f"Total: {report['total_bytes']:,} bytes across {report['file_count']:,} files.",
            "",
            "| Top-level path | Bytes | Files |",
            "|---|---:|---:|",
        ]
        lines.extend(
            f"| `{item['path']}` | {item['bytes']:,} | {item['files']:,} |"
            for item in report["top_level"][:12]
        )
        with args.github_summary.open("a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
