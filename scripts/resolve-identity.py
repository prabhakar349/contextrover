#!/usr/bin/env python3
"""Implements REQ-31a exactly — deterministic Behavior identity resolution.

Matching a Behavior found in a later Stage 1 run to its existing ID must be
deterministic and stdlib-only, never an agent judgement call, because T19
requires byte-identical IDs across consecutive runs. Algorithm, applied per
candidate in order:

  1. Anchor match — same interfaces[] set, same kind, and same
     evidence[0].locator file path with the line number stripped.
     Exactly one existing match -> reuse that ID.
  2. Content match — among existing Behaviors sharing the same interfaces[]
     set and kind, compute Jaccard similarity over lowercased alphanumeric
     tokens of summary, stopwords removed. Highest score >= 0.80 AND
     unique (no tie for that top score) -> reuse that ID.
  3. Otherwise — issue a new ID from state.json.counters.BHV. Counters only
     increase; an ID is never reused, even after deletion.

A Behavior present in an earlier run but not matched by any candidate this
run is never deleted. It is marked status: "unconfirmed" with
last_seen_run; removal requires a human Adjudication.

Candidates are sorted into a canonical order (by interfaces, kind, summary)
before resolution, and each existing Behavior can be claimed by at most one
candidate per run, so results are reproducible regardless of the order
candidates happen to arrive in.

Usage: python3 scripts/resolve-identity.py --candidates <path.json> [--dir .contextrover]
Writes .contextrover/inventory/behaviors.json and updates state.json's
counters.BHV and discovery_run.
"""
import argparse
import json
import re
from pathlib import Path

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being", "of", "to", "in",
    "on", "at", "for", "with", "by", "from", "and", "or", "but", "if", "then", "than", "that",
    "this", "these", "those", "it", "its", "as", "not", "no", "do", "does", "did", "has",
    "have", "had", "will", "would", "should", "can", "could", "may", "might", "must", "shall",
    "into", "over", "under", "when", "where", "which", "who", "whom",
}

TOKEN_RE = re.compile(r"[a-z0-9]+")


def load_json(path):
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def tokens(text):
    return {t for t in TOKEN_RE.findall((text or "").lower()) if t not in STOPWORDS}


def jaccard(a, b):
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def strip_line_number(locator):
    m = re.match(r"^(.*):(\d+)$", locator or "")
    return m.group(1) if m else locator


def anchor_key(behavior):
    ifc_set = frozenset(behavior.get("interfaces") or [])
    kind = behavior.get("kind")
    evidence = behavior.get("evidence") or []
    locator = evidence[0].get("locator") if evidence else None
    return (ifc_set, kind, strip_line_number(locator) if locator else None)


def bucket_key(behavior):
    return (frozenset(behavior.get("interfaces") or []), behavior.get("kind"))


def canonical_sort_key(candidate):
    return (sorted(candidate.get("interfaces") or []), candidate.get("kind") or "", candidate.get("summary") or "")


def resolve(existing, candidates, next_id_fn, current_run):
    """Returns (resolved_behaviors, new_id_count)."""
    available = list(existing)  # behaviors not yet claimed this run
    claimed_ids = set()
    resolved = []
    new_id_count = 0

    ordered_candidates = sorted(candidates, key=canonical_sort_key)

    for cand in ordered_candidates:
        match = None

        # Step 1 — anchor match
        cand_anchor = anchor_key(cand)
        anchor_matches = [e for e in available if anchor_key(e) == cand_anchor and e["id"] not in claimed_ids]
        if len(anchor_matches) == 1:
            match = anchor_matches[0]

        # Step 2 — content match
        if match is None:
            cand_bucket = bucket_key(cand)
            bucket_matches = [e for e in available if bucket_key(e) == cand_bucket and e["id"] not in claimed_ids]
            if bucket_matches:
                cand_tokens = tokens(cand.get("summary"))
                scored = [(jaccard(cand_tokens, tokens(e.get("summary"))), e) for e in bucket_matches]
                best_score = max(s for s, _ in scored)
                top = [e for s, e in scored if s == best_score]
                if best_score >= 0.80 and len(top) == 1:
                    match = top[0]

        if match is not None:
            # Start from the EXISTING record, not the candidate: later stages (Stage 2's
            # `context`, Stage 5's `spec_clauses`/`tests`, ...) add fields discovery never
            # produces. Overlaying the candidate's fresh findings on top refreshes what
            # discovery re-derives each run without erasing what later stages added --
            # a Stage 1 re-run must not silently wipe Stage 2's work.
            merged = dict(match)
            for key, val in cand.items():
                if val is not None:
                    merged[key] = val
            merged["id"] = match["id"]
            merged["status"] = "confirmed"
            merged["last_seen_run"] = current_run
            resolved.append(merged)
            claimed_ids.add(match["id"])
        else:
            # Step 3 — new ID
            new_id = next_id_fn()
            new_id_count += 1
            merged = dict(cand)
            merged["id"] = new_id
            merged["status"] = "confirmed"
            merged["last_seen_run"] = current_run
            resolved.append(merged)

    # Existing behaviors not claimed by any candidate this run -> unconfirmed, never deleted.
    # last_seen_run is left untouched: it already records the last run that actually confirmed them.
    for e in existing:
        if e["id"] not in claimed_ids:
            carried = dict(e)
            carried["status"] = "unconfirmed"
            resolved.append(carried)

    return resolved, new_id_count


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--candidates", required=True, help="Path to a JSON array of newly extracted Behavior candidates (no id yet)")
    parser.add_argument("--dir", default=".contextrover")
    args = parser.parse_args()

    base = Path(args.dir)
    candidates = load_json(Path(args.candidates)) or []

    inv_dir = base / "inventory"
    inv_dir.mkdir(parents=True, exist_ok=True)
    existing = load_json(inv_dir / "behaviors.json") or []

    state_path = base / "state.json"
    state = load_json(state_path) or {"version": "1", "stages": {}}
    counters = state.setdefault("counters", {})
    counter = counters.get("BHV", 0)
    current_run = state.get("discovery_run", 0) + 1

    def next_id_fn():
        nonlocal counter
        counter += 1
        return f"BHV-{counter:04d}"

    resolved, new_id_count = resolve(existing, candidates, next_id_fn, current_run)
    resolved.sort(key=lambda b: b["id"])

    with open(inv_dir / "behaviors.json", "w") as f:
        json.dump(resolved, f, indent=2, sort_keys=True)
        f.write("\n")

    counters["BHV"] = counter
    state["counters"] = counters
    state["discovery_run"] = current_run
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)
        f.write("\n")

    n_confirmed = sum(1 for b in resolved if b.get("status") == "confirmed")
    n_unconfirmed = sum(1 for b in resolved if b.get("status") == "unconfirmed")
    print(
        f"OK: {len(resolved)} Behaviors ({n_confirmed} confirmed, {n_unconfirmed} unconfirmed, "
        f"{new_id_count} newly issued); counters.BHV={counter}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
