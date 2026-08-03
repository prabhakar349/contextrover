#!/usr/bin/env python3
"""Executes the architecture fitness functions declared by a Slice's language pack.

Delegates to the pack's own tooling (ArchUnit for Java, go-arch-lint for Go,
import-linter for Python) via a documented invocation contract — this script
never reimplements fitness-rule logic itself.

Invocation contract (formalized in packs/PACK-INTERFACE.md at T13):
  packs/<language>/fitness.json:
    { "language": "<lang>",
      "rules": [ { "id": "...", "description": "...", "command": "..." }, ... ] }
  Each rule's `command` is split with shlex and run as a subprocess with cwd
  set to the target repository root. Exit code 0 = pass, non-zero = fail.
  `command` is the pack's own tooling invocation (an ArchUnit test runner,
  `go-arch-lint check`, `lint-imports`, ...) — this script only shells out
  and interprets the exit code; it does not parse or evaluate rule logic.

The target language is read from .contextrover/intake.json
estate.target_language (v1: one target language per Engagement — REQ-53
still holds, since source and target language are independent; source can
be polyglot via estate.source_languages[]).

Usage: python3 scripts/run-fitness.py [--dir .contextrover] [--repo .]
                                       [--pack-dir <path>] [--format text|json]
Exit 0 if every rule passes, 1 if any rule fails or the pack config is missing.
"""
import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PACKS_DIR = SCRIPT_DIR.parent / "packs"


def load_json(path):
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def resolve_pack_dir(base, override):
    if override:
        return Path(override)
    intake = load_json(base / "intake.json") or {}
    lang = (intake.get("estate") or {}).get("target_language")
    if not lang:
        return None
    return PACKS_DIR / lang


def run_rule(rule, repo_root):
    cmd = rule.get("command", "")
    rid = rule.get("id")
    desc = rule.get("description")
    try:
        args = shlex.split(cmd)
        result = subprocess.run(args, cwd=repo_root, capture_output=True, text=True, timeout=300)
        return {
            "id": rid, "description": desc, "passed": result.returncode == 0,
            "exit_code": result.returncode,
            "stdout_tail": result.stdout[-2000:], "stderr_tail": result.stderr[-2000:],
        }
    except FileNotFoundError as e:
        return {"id": rid, "description": desc, "passed": False, "exit_code": None, "error": f"command not found: {e}"}
    except subprocess.TimeoutExpired:
        return {"id": rid, "description": desc, "passed": False, "exit_code": None, "error": "timed out after 300s"}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dir", default=".contextrover")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--pack-dir", default=None)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    base = Path(args.dir)
    pack_dir = resolve_pack_dir(base, args.pack_dir)
    if not pack_dir or not (pack_dir / "fitness.json").exists():
        print(f"No fitness.json found for the target language pack (looked in {pack_dir})", file=sys.stderr)
        return 1

    manifest = load_json(pack_dir / "fitness.json") or {}
    results = [run_rule(r, args.repo) for r in manifest.get("rules", [])]

    if args.format == "json":
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            status = "PASS" if r["passed"] else "FAIL"
            print(f"[{status}] {r['id']}: {r.get('description', '')}")
            if not r["passed"] and r.get("error"):
                print(f"       {r['error']}")
        n_fail = sum(1 for r in results if not r["passed"])
        print(f"{len(results) - n_fail}/{len(results)} fitness rules passed")

    return 1 if any(not r["passed"] for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
