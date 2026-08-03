#!/usr/bin/env python3
"""Deterministic K-pass consensus aggregation for Stage 1 (Domain Discovery).

THE GAP THIS FIXES: rover-discover.md dispatches K independent passes (one
per framing: by-routes, by-tests, by-call-sites) of the same 9 discovery
agents, but nothing deterministic ever merged those K passes' raw candidates
into one deduplicated set with found-by-all/some/one partitioning -- that
step was previously left as prose ("union... partition...") for the main
session to improvise, which is neither reproducible nor testable, and
defeats the point of running an ensemble at all (Constitution C6): without
a real merge, the same interface found under two framings just looks like
two different candidates, and "found-by-all" never actually triggers.

Reads .contextrover/passes/<stage>/<framing>/<artifact-file>.json for every
framing present. For each of the 9 raw artifact types, clusters candidates
that plausibly describe the same real-world thing (deterministic matching,
stdlib only -- Constitution C5) and writes:

  .contextrover/consensus/<TYPE>.json
      One Consensus Run record (schemas/adjudication.schema.json,
      kind: "consensus-run") per artifact type: every merged candidate,
      which framings found it, its partition (all/some/one), an
      auto-decision (found-by-all -> accept; found-by-some/one -> triage,
      for the human review step 07-stages.md's Stage 1 gate requires), and
      the type's agreement_rate.

  .contextrover/passes/<stage>/merged/<artifact-file>.json
      The deduplicated, merged candidate records themselves (evidence
      unioned across every framing that found each one), ready to feed
      scripts/resolve-identity.py (Behaviors) or direct inventory assembly
      (everything else) once triage decisions are resolved by a human.

Interfaces and Divergences also get stable cross-run IDs here, from
state.json's already-reserved IFC_SYNC / IFC_ASYNC / DVG counters, using
the same anchor-then-content discipline as scripts/resolve-identity.py.
REQ-31's "IDs are stable across re-runs" was never actually implemented for
these types before this script -- REQ-31a's detailed algorithm was written
for Behaviors specifically, but the same discipline applies, and the
counters were already reserved in state.schema.json for exactly this.
Behaviors are deliberately NOT ID-assigned here -- that stays
scripts/resolve-identity.py's job, called separately on this script's
merged behaviors.json output, exactly as rover-discover.md documents.

Usage: python3 scripts/consensus.py --stage 1 [--dir .contextrover]
"""
import argparse
import datetime
import json
import re
import sys
from pathlib import Path

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being", "of", "to", "in",
    "on", "at", "for", "with", "by", "from", "and", "or", "but", "if", "then", "than", "that",
    "this", "these", "those", "it", "its", "as", "not", "no", "do", "does", "did", "has",
    "have", "had", "will", "would", "should", "can", "could", "may", "might", "must", "shall",
    "into", "over", "under", "when", "where", "which", "who", "whom",
}
TOKEN_RE = re.compile(r"[a-z0-9]+")


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


def load_json(path):
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Match predicates -- one per raw artifact type. Deterministic, stdlib only.
# ---------------------------------------------------------------------------
def match_behaviors(a, b):
    if frozenset(a.get("interfaces") or []) != frozenset(b.get("interfaces") or []):
        return False
    if a.get("kind") != b.get("kind"):
        return False
    a_ev, b_ev = a.get("evidence") or [], b.get("evidence") or []
    a_loc = strip_line_number(a_ev[0]["locator"]) if a_ev else None
    b_loc = strip_line_number(b_ev[0]["locator"]) if b_ev else None
    if a_loc and a_loc == b_loc:
        return True
    return jaccard(tokens(a.get("summary")), tokens(b.get("summary"))) >= 0.80


def match_interfaces(a, b):
    if a.get("kind") != b.get("kind"):
        return False
    a_sync, b_sync = a.get("sync") or {}, b.get("sync") or {}
    if a_sync.get("method") and (a_sync.get("method"), a_sync.get("path")) == (b_sync.get("method"), b_sync.get("path")):
        return True
    a_async, b_async = a.get("async") or {}, b.get("async") or {}
    if a_async.get("topic") and a_async.get("topic") == b_async.get("topic"):
        return True
    return bool(a.get("name")) and a.get("name") == b.get("name") and a.get("owning_service") == b.get("owning_service")


BHV_ID_RE = re.compile(r"^BHV-[0-9]{4}$")


def match_divergences(a, b):
    if jaccard(tokens(a.get("concept")), tokens(b.get("concept"))) >= 0.80:
        return True
    # Only a real, resolved Behavior ID counts as shared evidence -- "unknown" or any
    # other placeholder must never act as a matching key (it would spuriously merge
    # every divergence still awaiting behavior_id resolution, regardless of concept).
    a_bids = {v.get("behavior_id") for v in a.get("variants") or [] if v.get("behavior_id") and BHV_ID_RE.match(v["behavior_id"])}
    b_bids = {v.get("behavior_id") for v in b.get("variants") or [] if v.get("behavior_id") and BHV_ID_RE.match(v["behavior_id"])}
    return bool(a_bids & b_bids)


def match_coupling(a, b):
    return frozenset([a.get("entity_a"), a.get("entity_b")]) == frozenset([b.get("entity_a"), b.get("entity_b")])


def match_sequences(a, b):
    return tuple(a.get("steps") or []) == tuple(b.get("steps") or [])


def match_redaction(a, b):
    return bool(a.get("interface")) and a.get("interface") == b.get("interface")


def match_dependencies(a, b):
    return a.get("caller") == b.get("caller") and a.get("callee") == b.get("callee")


def match_consumers(a, b):
    return a.get("interface") == b.get("interface") and (a.get("consumer") or {}).get("identifier") == (b.get("consumer") or {}).get("identifier")


TYPE_MATCHERS = {
    "behaviors.json": match_behaviors,
    "interfaces-sync.json": match_interfaces,
    "interfaces-async.json": match_interfaces,
    "divergences.json": match_divergences,
    "coupling.json": match_coupling,
    "sequences.json": match_sequences,
    "redaction-policy.json": match_redaction,
    "dependencies.json": match_dependencies,
    "consumers.json": match_consumers,
}


# ---------------------------------------------------------------------------
# Clustering (union-find) and deterministic merge
# ---------------------------------------------------------------------------
def cluster(items_with_framing, match_fn):
    n = len(items_with_framing)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    for i in range(n):
        for j in range(i + 1, n):
            if match_fn(items_with_framing[i][1], items_with_framing[j][1]):
                union(i, j)

    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(items_with_framing[i])
    return list(groups.values())


def merge_record(cluster_items):
    """Merge N (framing, dict) pairs describing the same thing. List fields are
    unioned+deduped; scalar fields take the alphabetically-first framing's
    value where the running merge hasn't already filled that key -- fully
    deterministic regardless of input order."""
    ordered = sorted(cluster_items, key=lambda fi: fi[0])
    merged = dict(ordered[0][1])
    for _framing, rec in ordered[1:]:
        for key, val in rec.items():
            if isinstance(val, list) and isinstance(merged.get(key), list):
                existing = merged[key]
                for item in val:
                    if item not in existing:
                        existing.append(item)
            elif merged.get(key) is None:
                merged[key] = val
    if isinstance(merged.get("evidence"), list):
        seen = set()
        deduped = []
        for ev in merged["evidence"]:
            k = (ev.get("source"), ev.get("locator"))
            if k not in seen:
                seen.add(k)
                deduped.append(ev)
        merged["evidence"] = deduped
    return merged


def partition_of(found_by, all_framings):
    if set(found_by) == set(all_framings):
        return "all"
    if len(found_by) > 1:
        return "some"
    return "one"


def candidate_label(record, type_name):
    """Short deterministic label for the consensus record -- not a final
    artifact ID. Final IDs come from scripts/resolve-identity.py (Behaviors)
    or assign_stable_ids() below (Interfaces, Divergences)."""
    if type_name.startswith("behaviors"):
        return (record.get("summary") or "")[:60]
    if type_name.startswith("interfaces"):
        return record.get("name") or (record.get("async") or {}).get("topic") or ""
    if type_name.startswith("divergences"):
        return record.get("concept") or ""
    if type_name.startswith("coupling"):
        return f"{record.get('entity_a')}<->{record.get('entity_b')}"
    if type_name.startswith("sequences"):
        return "->".join(record.get("steps") or [])
    if type_name.startswith("redaction"):
        return record.get("interface") or ""
    if type_name.startswith("dependencies"):
        return f"{record.get('caller')}->{record.get('callee')}"
    if type_name.startswith("consumers"):
        return f"{record.get('interface')}:{(record.get('consumer') or {}).get('identifier')}"
    return ""


def aggregate_type(type_name, candidates_by_framing, all_framings):
    matcher = TYPE_MATCHERS[type_name]
    items = [(framing, c) for framing, lst in candidates_by_framing.items() for c in lst]
    clusters = cluster(items, matcher)

    merged_records, consensus_candidates = [], []
    for c in clusters:
        found_by = sorted({framing for framing, _ in c})
        merged = merge_record(c)
        partition = partition_of(found_by, all_framings)
        merged_records.append(merged)
        consensus_candidates.append({
            "candidate_id": candidate_label(merged, type_name),
            "found_by": found_by,
            "partition": partition,
            "decision": "accept" if partition == "all" else "triage",
        })

    order = sorted(range(len(merged_records)), key=lambda i: consensus_candidates[i]["candidate_id"])
    merged_records = [merged_records[i] for i in order]
    consensus_candidates = [consensus_candidates[i] for i in order]

    total = len(consensus_candidates)
    all_count = sum(1 for c in consensus_candidates if c["partition"] == "all")
    agreement_rate = (all_count / total) if total else 0.0
    return merged_records, consensus_candidates, agreement_rate


# ---------------------------------------------------------------------------
# Cross-run stable ID assignment (Interfaces, Divergences) -- REQ-31
# ---------------------------------------------------------------------------
def assign_stable_ids(merged_records, existing_records, prefix, counters, counter_key, match_fn):
    counter = counters.get(counter_key, 0)
    claimed = set()
    out = []
    for rec in merged_records:
        candidates = [e for e in existing_records if e.get("id") not in claimed and match_fn(rec, e)]
        new_rec = dict(rec)
        if len(candidates) == 1:
            new_rec["id"] = candidates[0]["id"]
            claimed.add(candidates[0]["id"])
        else:
            counter += 1
            new_rec["id"] = f"{prefix}-{counter:04d}"
        out.append(new_rec)
    counters[counter_key] = counter
    return out


IFC_ID_RE = re.compile(r"^IFC-(SYNC|ASYNC)-[0-9]{4}$")


def build_name_to_id(interface_records):
    """A candidate written before consensus has no interface ID to cite yet --
    agents cite interfaces by name/path/topic instead (per their own prompts).
    Once Interfaces are ID-assigned, resolve those name-shaped references."""
    m = {}
    for rec in interface_records:
        rid = rec.get("id")
        if not rid:
            continue
        if rec.get("name"):
            m[rec["name"]] = rid
        sync = rec.get("sync") or {}
        if sync.get("method") and sync.get("path"):
            m[f"{sync['method']} {sync['path']}"] = rid
        topic = (rec.get("async") or {}).get("topic")
        if topic:
            m[topic] = rid
    return m


def resolve_interface_refs(value, name_to_id):
    if IFC_ID_RE.match(value):
        return value
    return name_to_id.get(value, value)  # leave unresolved refs as-is -- the gate catches them (C10)


def resolve_behavior_interface_names(records, name_to_id):
    for rec in records:
        if rec.get("interfaces"):
            rec["interfaces"] = [resolve_interface_refs(v, name_to_id) for v in rec["interfaces"]]
    return records


def resolve_sequence_steps(records, name_to_id):
    for rec in records:
        if rec.get("steps"):
            rec["steps"] = [resolve_interface_refs(v, name_to_id) for v in rec["steps"]]
    return records


def resolve_interface_field(records, name_to_id):
    for rec in records:
        if rec.get("interface"):
            rec["interface"] = resolve_interface_refs(rec["interface"], name_to_id)
    return records


# Interfaces and Divergences must be ID-assigned before anything that cites them
# by name (Behaviors, Sequences) is finalized.
PROCESSING_ORDER = [
    "interfaces-sync.json", "interfaces-async.json", "divergences.json",
    "behaviors.json", "coupling.json", "consumers.json", "dependencies.json",
    "redaction-policy.json", "sequences.json",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stage", type=int, default=1)
    parser.add_argument("--dir", default=".contextrover")
    args = parser.parse_args()

    base = Path(args.dir)
    passes_dir = base / "passes" / str(args.stage)
    if not passes_dir.exists():
        print(f"No passes found under {passes_dir}", file=sys.stderr)
        return 1

    all_framings = sorted(p.name for p in passes_dir.iterdir() if p.is_dir() and p.name != "merged")
    if not all_framings:
        print(f"No framing directories found under {passes_dir}", file=sys.stderr)
        return 1

    state_path = base / "state.json"
    state = load_json(state_path) or {"version": "1", "stages": {}}
    counters = state.setdefault("counters", {})

    existing_interfaces = load_json(base / "inventory" / "interfaces.json") or []
    existing_divergences = load_json(base / "inventory" / "divergences.json") or []

    merged_dir = passes_dir / "merged"
    merged_dir.mkdir(parents=True, exist_ok=True)
    consensus_dir = base / "consensus"
    consensus_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    summary = []
    name_to_id = {}

    for type_name in PROCESSING_ORDER:
        candidates_by_framing = {}
        for framing in all_framings:
            data = load_json(passes_dir / framing / type_name)
            if data:
                candidates_by_framing[framing] = data
        if not candidates_by_framing:
            continue

        merged_records, consensus_candidates, agreement_rate = aggregate_type(type_name, candidates_by_framing, all_framings)

        if type_name == "interfaces-sync.json":
            merged_records = assign_stable_ids(merged_records, existing_interfaces, "IFC-SYNC", counters, "IFC_SYNC", match_interfaces)
            name_to_id.update(build_name_to_id(merged_records))
        elif type_name == "interfaces-async.json":
            merged_records = assign_stable_ids(merged_records, existing_interfaces, "IFC-ASYNC", counters, "IFC_ASYNC", match_interfaces)
            name_to_id.update(build_name_to_id(merged_records))
        elif type_name == "divergences.json":
            merged_records = assign_stable_ids(merged_records, existing_divergences, "DVG", counters, "DVG", match_divergences)
        elif type_name == "behaviors.json":
            merged_records = resolve_behavior_interface_names(merged_records, name_to_id)
        elif type_name in ("redaction-policy.json", "consumers.json"):
            merged_records = resolve_interface_field(merged_records, name_to_id)
        elif type_name == "sequences.json":
            merged_records = resolve_sequence_steps(merged_records, name_to_id)
            for i, r in enumerate(merged_records, start=1):
                r["id"] = f"SEQ-{i:04d}"  # fresh each run; nothing else cites a sequence ID

        with open(merged_dir / type_name, "w") as f:
            json.dump(merged_records, f, indent=2, sort_keys=True)
            f.write("\n")

        label = type_name.replace(".json", "").upper()
        record = {
            "id": "ADJ-0000",
            "stage": args.stage,
            "k": len(all_framings),
            "framings": all_framings,
            "candidates": consensus_candidates,
            "kind": "consensus-run",
            "decided_by": "consensus.py (mechanical)",
            "decided_at": now,
            "agreement_rate": round(agreement_rate, 4),
        }
        with open(consensus_dir / f"CONSENSUS-{label}.json", "w") as f:
            json.dump(record, f, indent=2, sort_keys=True)
            f.write("\n")

        summary.append((type_name, len(merged_records), agreement_rate))

    state["counters"] = counters
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)
        f.write("\n")

    if not summary:
        print(f"No raw candidate files found under {passes_dir}/<framing>/", file=sys.stderr)
        return 1

    for type_name, n, rate in summary:
        print(f"OK: {type_name}: {n} merged candidate(s), agreement_rate={rate:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
