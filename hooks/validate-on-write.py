#!/usr/bin/env python3
"""PostToolUse hook: after a Write/Edit touching .contextrover/**, run
validate-artifacts.py and block the turn if it fails (T15).

Reads the standard PostToolUse hook JSON payload from stdin. Emits hook
JSON output on stdout — {"decision": "block", "reason": "..."} — only when
validation fails; prints nothing otherwise (Constitution C5: computation
lives in one committed, reviewed script, not an ad-hoc inline command).
"""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
VALIDATE_SCRIPT = SCRIPT_DIR.parent / "scripts" / "validate-artifacts.py"


def touches_contextrover(file_path):
    normalized = (file_path or "").replace("\\", "/")
    return ".contextrover/" in normalized or normalized.rstrip("/").endswith(".contextrover")


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    tool_input = payload.get("tool_input") or {}
    tool_response = payload.get("tool_response") or {}
    file_path = tool_input.get("file_path") or tool_response.get("filePath") or ""

    if not touches_contextrover(file_path):
        return 0

    result = subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), "--dir", ".contextrover"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        reason = (
            "scripts/validate-artifacts.py failed after a write under .contextrover/:\n"
            + (result.stderr or "") + (result.stdout or "")
        )
        print(json.dumps({"decision": "block", "reason": reason}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
