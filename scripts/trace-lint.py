#!/usr/bin/env python3
"""The traceability gate — scripts/trace-lint.py.

Implements every criterion 07-stages.md §3 attributes to trace-lint.py,
per stage, plus the generic [record] check (Build Constitution C2 escape
hatch: a schema-valid approval/adjudication record exists naming a human
decider, bound to the artifact's current content hash).

Two numeric thresholds are needed nowhere else in the spec pack — the
Stage 3 "configured maximum size" and the Stage 6 coverage threshold.
No value is given anywhere in specs/ or knowledge/ to derive one from, so
these are seeded here the same way 11-estimation.md seeds behaviors_per_pr,
f_failure and f_async: a documented default, overridable, recalibrated
later. Override via .contextrover/state.json:
  { "gate_config": { "max_slice_work_units": 40, "coverage_threshold": 0.9 } }

Boundary span (a Behavior touching >1 target service) is a warning, not
an error — sagas are legitimate. Warnings never fail the gate.

Usage: python3 scripts/trace-lint.py [--stage N] [--format text|json] [--dir .contextrover]
Exit 0 clean, 1 if any error-level finding exists.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

DEFAULT_MAX_SLICE_WORK_UNITS = 40   # behaviors + failure_path_behaviors*1.5 + interfaces_sync + interfaces_async*2.0
DEFAULT_COVERAGE_THRESHOLD = 0.90   # fraction of a Slice's Behaviors needing a passing characterization test


def load_json(path):
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def sha256_of(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


class Findings:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, code, message):
        self.errors.append({"level": "error", "code": code, "message": message})

    def warn(self, code, message):
        self.warnings.append({"level": "warning", "code": code, "message": message})


def load_config(base):
    state = load_json(base / "state.json") or {}
    overrides = state.get("gate_config", {})
    return {
        "max_slice_work_units": overrides.get("max_slice_work_units", DEFAULT_MAX_SLICE_WORK_UNITS),
        "coverage_threshold": overrides.get("coverage_threshold", DEFAULT_COVERAGE_THRESHOLD),
    }


def slice_records(base):
    """{slice_id: (slice_dir, slice_record)} for every slices/<id>/slice.json present."""
    out = {}
    slices_dir = base / "slices"
    if not slices_dir.exists():
        return out
    for sd in sorted(slices_dir.glob("*")):
        rec = load_json(sd / "slice.json")
        if rec:
            out[rec.get("id", sd.name)] = (sd, rec)
    return out


def adjudications_for_stage(base, stage):
    adj_dir = base / "adjudications"
    if not adj_dir.exists():
        return []
    out = []
    for p in sorted(adj_dir.glob("*.json")):
        rec = load_json(p)
        if rec and rec.get("stage") == stage and rec.get("kind") == "adjudication":
            out.append(rec)
    return out


# ---------------------------------------------------------------------------
# Stage 1 — Domain Discovery
# ---------------------------------------------------------------------------
def run_stage1(base, cfg, f):
    behaviors = load_json(base / "inventory/behaviors.json") or []
    interfaces = load_json(base / "inventory/interfaces.json") or []

    for b in behaviors:
        bid = b.get("id") or "<missing id>"
        if not b.get("id"):
            f.error("S1-BHV-ID", f"Behavior has no id: {b!r}")
        if not b.get("evidence"):
            f.error("S1-BHV-EVIDENCE", f"Behavior {bid} has no evidence entries")

    for i in interfaces:
        if i.get("kind") in ("async-published", "async-consumed"):
            iid = i.get("id") or "<missing id>"
            consumers = i.get("consumers") or []
            complete = i.get("consumers_complete")
            if not consumers and complete is not False:
                f.error(
                    "S1-ASYNC-CONSUMERS",
                    f"Async Interface {iid} has no consumer evidence and consumers_complete "
                    f"is not explicitly false (REQ-02)",
                )

    consensus_dir = base / "consensus"
    consensus_files = sorted(consensus_dir.glob("*.json")) if consensus_dir.exists() else []
    if not consensus_files:
        f.error("S1-AGREEMENT", "No consensus/*.json records found — agreement rate not computed")
    else:
        for cf in consensus_files:
            rec = load_json(cf)
            if rec is None or rec.get("agreement_rate") is None:
                f.error("S1-AGREEMENT", f"{cf}: agreement_rate not recorded")

    # [record] — found-by-one list reviewed
    reviewed = adjudications_for_stage(base, 1)
    if not reviewed:
        f.error(
            "S1-RECORD-FOUND-BY-ONE",
            "No stage-1 Adjudication record found — the found-by-one list must be reviewed "
            "and signed by a human decider",
        )


# ---------------------------------------------------------------------------
# Stage 2 — Strategic Design
# ---------------------------------------------------------------------------
def run_stage2(base, cfg, f):
    behaviors = load_json(base / "inventory/behaviors.json") or []
    contexts = load_json(base / "model/contexts.json") or []
    divergences = load_json(base / "inventory/divergences.json") or []
    ctx_ids = {c["id"] for c in contexts if c.get("id")}

    for b in behaviors:
        bid = b.get("id") or "<missing id>"
        ctx = b.get("context")
        if not ctx:
            f.error("S2-ORPHAN-BEHAVIOR", f"Orphan Behavior {bid}: no Context assigned")
        elif ctx not in ctx_ids:
            f.error("S2-DANGLING-CONTEXT", f"Behavior {bid} references unknown Context {ctx}")

        target_services = b.get("target_services") or []
        if len(target_services) > 1:
            f.warn(
                "S2-BOUNDARY-SPAN",
                f"Behavior {bid} touches {len(target_services)} target services "
                f"{target_services} — sagas are legitimate; verify this is one",
            )

    for d in divergences:
        did = d.get("id") or "<missing id>"
        classification = d.get("classification")
        if not classification or classification == "unclassified":
            f.error("S2-UNCLASSIFIED-DIVERGENCE", f"Divergence {did} is unclassified")
        elif not d.get("decision_owner"):
            f.error(
                "S2-RECORD-DIVERGENCE",
                f"Divergence {did} is classified {classification!r} but has no decision_owner recorded",
            )

    for c in contexts:
        cid = c.get("id") or "<missing id>"
        if not c.get("aggregate_roots"):
            f.error("S2-NO-AGGREGATE-ROOT", f"Context {cid} owns no aggregate root")

    # [record] — signed Adjudication per boundary decision
    if not adjudications_for_stage(base, 2):
        f.error(
            "S2-RECORD-BOUNDARY",
            "No stage-2 Adjudication record found for the boundary decision",
        )


# ---------------------------------------------------------------------------
# Stage 3 — Solution Outline
# ---------------------------------------------------------------------------
def run_stage3(base, cfg, f):
    behaviors = load_json(base / "inventory/behaviors.json") or []
    slices = slice_records(base)

    claims = {}
    for sid, (sd, rec) in slices.items():
        for bid in rec.get("behaviors", []):
            claims.setdefault(bid, []).append(sid)

    for b in behaviors:
        bid = b.get("id") or "<missing id>"
        owners = claims.get(bid, [])
        if len(owners) == 0:
            f.error("S3-UNASSIGNED-BEHAVIOR", f"Behavior {bid} is not assigned to any Slice")
        elif len(owners) > 1:
            f.error(
                "S3-MULTI-ASSIGNED-BEHAVIOR",
                f"Behavior {bid} is assigned to more than one Slice: {owners}",
            )

    for sid, (sd, rec) in slices.items():
        ac = load_json(sd / "acceptance-criteria.json")
        if not ac:
            f.error("S3-NO-ACCEPTANCE-CRITERIA", f"Slice {sid} has no acceptance-criteria.json (or it is empty)")

        size = load_json(sd / "size.json")
        if not size:
            f.error("S3-NO-SIZE", f"Slice {sid} has no size.json")
        else:
            work_units = (
                size.get("behaviors", 0)
                + size.get("failure_path_behaviors", 0) * 1.5
                + size.get("interfaces_sync", 0)
                + size.get("interfaces_async", 0) * 2.0
            )
            if work_units > cfg["max_slice_work_units"]:
                f.error(
                    "S3-OVERSIZED-SLICE",
                    f"Slice {sid} exceeds max size: {work_units:.1f} work units > "
                    f"{cfg['max_slice_work_units']} (behaviors + failure_path*1.5 + interfaces_sync "
                    f"+ interfaces_async*2.0); must be split before roadmapping",
                )

        strategy = rec.get("oracle_strategy")
        if strategy == "specification":
            f.error("S3-ORACLE-STRATEGY", f"Slice {sid}: Specification oracle is not implemented in this version.")
        elif strategy != "characterization":
            f.error(
                "S3-ORACLE-STRATEGY",
                f"Slice {sid}: oracle_strategy must be 'characterization' in v1, got {strategy!r}",
            )


# ---------------------------------------------------------------------------
# Stage 4 — Delivery Roadmap
# ---------------------------------------------------------------------------
def run_stage4(base, cfg, f):
    roadmap_path = base / "roadmap.json"
    roadmap = load_json(roadmap_path)
    if not roadmap:
        f.error("S4-NO-ROADMAP", "roadmap.json not found")
        return

    all_slice_ids = {rec["id"] for rec in (r for _, r in slice_records(base).values()) if rec.get("id")}

    seen = {}
    for inc in roadmap.get("increments", []):
        for sid in inc.get("slices", []):
            seen.setdefault(sid, []).append(inc.get("ordinal"))
        if not inc.get("owner"):
            f.error("S4-NO-OWNER", f"Increment {inc.get('ordinal')} has no named owner")

    for sid in all_slice_ids:
        occurrences = seen.get(sid, [])
        if len(occurrences) == 0:
            f.error("S4-SLICE-MISSING-FROM-ROADMAP", f"Slice {sid} does not appear in the roadmap")
        elif len(occurrences) > 1:
            f.error(
                "S4-SLICE-DUPLICATED-IN-ROADMAP",
                f"Slice {sid} appears in the roadmap more than once: increments {occurrences}",
            )

    increments = sorted(roadmap.get("increments", []), key=lambda i: i.get("ordinal", -1))
    if not increments or increments[0].get("ordinal") != 0 or not increments[0].get("is_walking_skeleton"):
        f.error("S4-INCREMENT-0", "Increment 0 must exist, have ordinal 0, and be flagged is_walking_skeleton")

    if not (roadmap.get("capacity") or {}).get("binding_constraint"):
        f.error("S4-NO-BINDING-CONSTRAINT", "roadmap.json capacity.binding_constraint is not named")

    # [record] — leadership approval bound to roadmap's version hash
    approvals = load_json(base / "approvals.json") or []
    current_hash = sha256_of(roadmap_path)
    matches = [a for a in approvals if a.get("artifact") == "roadmap.json" and a.get("version_hash") == current_hash]
    if not matches:
        f.error(
            "S4-RECORD-LEADERSHIP-APPROVAL",
            f"No leadership approval in approvals.json bound to roadmap.json's current hash "
            f"({current_hash}) — roadmap is stale or unapproved",
        )


# ---------------------------------------------------------------------------
# Stage 5 — Tactical Design
# ---------------------------------------------------------------------------
def run_stage5(base, cfg, f):
    interfaces_by_id = {i["id"]: i for i in (load_json(base / "inventory/interfaces.json") or []) if i.get("id")}
    behaviors_by_id = {b["id"]: b for b in (load_json(base / "inventory/behaviors.json") or []) if b.get("id")}

    for sid, (sd, rec) in slice_records(base).items():
        tm_path = sd / "tactical-model.json"
        tm = load_json(tm_path)
        if not tm:
            continue  # Slice has not reached Tactical Design yet

        cited_behaviors = set()
        for agg in tm.get("aggregates", []):
            invariants = agg.get("invariants", [])
            if not invariants:
                f.error("S5-NO-INVARIANT", f"Slice {sid} aggregate {agg.get('name')} declares no invariants")
            for inv in invariants:
                bs = inv.get("behaviors") or []
                if not bs:
                    f.error(
                        "S5-UNCITED-CLAUSE",
                        f"Slice {sid} aggregate {agg.get('name')} invariant "
                        f"{inv.get('statement')!r} cites no Behavior ID",
                    )
                cited_behaviors.update(bs)

        for bid in rec.get("behaviors", []):
            if bid not in cited_behaviors:
                f.error(
                    "S5-ORPHAN-BEHAVIOR-IN-SLICE",
                    f"Slice {sid}: Behavior {bid} is assigned to the Slice but addressed by no invariant",
                )

        slice_interfaces = set()
        for bid in rec.get("behaviors", []):
            b = behaviors_by_id.get(bid)
            if b:
                slice_interfaces.update(b.get("interfaces", []))

        adapters_dir = sd / "adapters"
        for ifc_id in sorted(slice_interfaces):
            adapter_file = adapters_dir / f"{ifc_id}.md"
            if not adapter_file.exists():
                f.error("S5-NO-ADAPTER", f"Slice {sid}: legacy Interface {ifc_id} has no adapter spec ({adapter_file})")
            elif not re.search(r"(?im)^Owner:\s*\S", adapter_file.read_text()):
                f.error(
                    "S5-NO-ADAPTER-OWNER",
                    f"Slice {sid}: adapter spec {adapter_file} has no named owner "
                    f"(expected a line matching 'Owner: <name>')",
                )

        # [record] — architecture review approval bound to tactical-model.json's version hash
        approvals = rec.get("approvals") or []
        current_hash = sha256_of(tm_path)
        matches = [a for a in approvals if a.get("version_hash") == current_hash]
        if not matches:
            f.error(
                "S5-RECORD-ARCH-REVIEW",
                f"Slice {sid}: no architecture review approval bound to tactical-model.json's "
                f"current hash ({current_hash})",
            )


# ---------------------------------------------------------------------------
# Stage 6 — Verification Design
# ---------------------------------------------------------------------------
def run_stage6(base, cfg, f):
    redaction_by_ifc = {
        r["interface"]: r for r in (load_json(base / "inventory/redaction-policy.json") or []) if r.get("interface")
    }
    behaviors_by_id = {b["id"]: b for b in (load_json(base / "inventory/behaviors.json") or []) if b.get("id")}

    for sid, (sd, rec) in slice_records(base).items():
        cov = load_json(sd / "verification" / "coverage.json")
        if not cov:
            continue  # Slice has not reached Verification Design yet

        if rec.get("oracle_strategy") == "characterization":
            slice_interfaces = set()
            for bid in rec.get("behaviors", []):
                b = behaviors_by_id.get(bid)
                if b:
                    slice_interfaces.update(b.get("interfaces", []))
            for ifc_id in sorted(slice_interfaces):
                r = redaction_by_ifc.get(ifc_id)
                if not r:
                    f.error("S6-NO-REDACTION-ASSESSMENT", f"Slice {sid}: Interface {ifc_id} has no Redaction Policy assessment")
                elif r.get("verdict") != "GO":
                    f.error(
                        "S6-REDACTION-NOGO",
                        f"Slice {sid}: Interface {ifc_id} Redaction Policy verdict is {r.get('verdict')!r}, not GO "
                        f"(seam S1.3 — this gate applies because oracle_strategy is characterization)",
                    )

        total = cov.get("total", 0)
        covered = cov.get("covered", 0)
        ratio = (covered / total) if total else 0
        if ratio < cfg["coverage_threshold"]:
            f.error(
                "S6-COVERAGE-BELOW-THRESHOLD",
                f"Slice {sid}: coverage {covered}/{total} ({ratio:.0%}) is below threshold "
                f"{cfg['coverage_threshold']:.0%}",
            )

        if cov.get("failure_path") is None:
            f.error("S6-NO-FAILURE-PATH-COVERAGE", f"Slice {sid}: coverage.json does not report failure_path coverage separately")


# ---------------------------------------------------------------------------
# Stage 8 — Transition ([record] only; other criteria belong to status-report.py)
# ---------------------------------------------------------------------------
def run_stage8(base, cfg, f):
    contexts_dir = base / "contexts"
    if not contexts_dir.exists():
        return
    approvals = load_json(base / "approvals.json") or []
    for cd in sorted(contexts_dir.glob("*")):
        cid = cd.name
        checklist = cd / "decommission-checklist.md"
        if not checklist.exists():
            continue  # not yet at the decommission step
        artifact_key = f"contexts/{cid}/decommission-checklist.md"
        current_hash = sha256_of(checklist)
        matches = [a for a in approvals if a.get("artifact") == artifact_key and a.get("version_hash") == current_hash]
        if not matches:
            f.error(
                "S8-RECORD-DECOMMISSION",
                f"Context {cid}: no approval bound to decommission-checklist.md's current hash ({current_hash})",
            )


STAGE_FUNCS = {1: run_stage1, 2: run_stage2, 3: run_stage3, 4: run_stage4, 5: run_stage5, 6: run_stage6, 8: run_stage8}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stage", type=int, choices=range(0, 9), default=None)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--dir", default=".contextrover")
    args = parser.parse_args()

    base = Path(args.dir)
    cfg = load_config(base)
    f = Findings()

    stages = [args.stage] if args.stage is not None else sorted(STAGE_FUNCS)
    for s in stages:
        fn = STAGE_FUNCS.get(s)
        if fn:
            fn(base, cfg, f)

    if args.format == "json":
        print(json.dumps({"errors": f.errors, "warnings": f.warnings}, indent=2))
    else:
        for w in f.warnings:
            print(f"WARN  [{w['code']}] {w['message']}")
        for e in f.errors:
            print(f"ERROR [{e['code']}] {e['message']}", file=sys.stderr)
        summary = f"{len(f.errors)} error(s), {len(f.warnings)} warning(s)"
        print(summary, file=sys.stderr if f.errors else sys.stdout)

    return 1 if f.errors else 0


if __name__ == "__main__":
    sys.exit(main())
