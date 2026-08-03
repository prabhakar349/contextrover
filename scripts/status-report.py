#!/usr/bin/env python3
"""Rolls up Engagement / Context / Slice / Workstream state — scripts/status-report.py.

No network access (REQ-32): this script must never import urllib, socket,
http, or requests, and never open a network connection. Local files only.

Reports: per-stage status; Build Stream conformity % (legacy-surface
characterization coverage); Consumer Migration Stream adoption %
(new-surface adoption) — reported separately, never blended (REQ-13);
ensemble agreement distribution (found-by-all/some/one); Divergences by
classification; unresolved high risks; count of Interfaces with
sunset_authority: null.

Usage: python3 scripts/status-report.py [--dir .contextrover] [--format text|json]
"""
import argparse
import json
from pathlib import Path


def load_json(path):
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def stage_status(base):
    state = load_json(base / "state.json") or {}
    stages = state.get("stages", {})
    return {str(n): stages.get(str(n), {}).get("status", "not-started") for n in range(9)}


def build_stream_conformity(base):
    """REQ-12: % of Behavior IDs with a passing characterization test, aggregated across Slices."""
    total = passing = 0
    slices_dir = base / "slices"
    if slices_dir.exists():
        for sd in sorted(slices_dir.glob("*")):
            cov = load_json(sd / "verification" / "coverage.json")
            if cov:
                total += cov.get("total", 0)
                passing += cov.get("passing", 0)
    pct = (passing / total * 100) if total else None
    return {"passing": passing, "total": total, "percent": pct}


def consumer_migration_adoption(base):
    """Legacy Interfaces no longer carrying traffic, out of all tracked legacy Interfaces."""
    retirement = load_json(base / "retirement.json") or []
    total = len(retirement)
    adopted = sum(1 for r in retirement if r.get("status") in ("zero-traffic", "retired"))
    pct = (adopted / total * 100) if total else None
    return {"adopted": adopted, "total": total, "percent": pct}


def agreement_distribution(base):
    """Constitution C6 partition: found-by-all (auto-accept), found-by-some (triage), found-by-one (inspect)."""
    dist = {"all": 0, "some": 0, "one": 0}
    for kind_dir in ("consensus", "adjudications"):
        d = base / kind_dir
        if not d.exists():
            continue
        for p in sorted(d.glob("*.json")):
            rec = load_json(p)
            if not rec:
                continue
            for c in rec.get("candidates", []):
                part = c.get("partition")
                if part in dist:
                    dist[part] += 1
    return dist


def divergences_by_classification(base):
    divergences = load_json(base / "inventory" / "divergences.json") or []
    counts = {}
    for d in divergences:
        c = d.get("classification") or "unclassified"
        counts[c] = counts.get(c, 0) + 1
    return counts


def unresolved_high_risks(base):
    """06-intake.md §5: every high risk stays listed until resolved or explicitly accepted
    with a recorded rationale. 'Resolved' has no dedicated schema field — a risk that no
    longer applies simply stops being recomputed into intake.json.derived.risks on re-entry.
    'Accepted' is recognized here as an approvals.json record whose criterion names the risk id."""
    intake = load_json(base / "intake.json") or {}
    risks = (intake.get("derived") or {}).get("risks") or []
    approvals = load_json(base / "approvals.json") or []
    accepted_risk_ids = {
        r["id"]
        for a in approvals
        for r in risks
        if r.get("id") and r["id"] in (a.get("criterion") or "")
    }
    return [r for r in risks if r.get("severity") == "high" and r.get("id") not in accepted_risk_ids]


def interfaces_permanent(base):
    """sunset_authority: null is the leading indicator the Consumer Migration Stream never finishes."""
    retirement = load_json(base / "retirement.json") or []
    return sum(1 for r in retirement if r.get("sunset_authority") is None)


def waypoints_at_risk(base):
    """Extension beyond the base spec pack: Migration Waypoints not on track."""
    waypoints = load_json(base / "migration-waypoints.json") or []
    return [w for w in waypoints if w.get("status") in ("at-risk", "missed")]


def build_report(base):
    return {
        "stages": stage_status(base),
        "build_stream_conformity": build_stream_conformity(base),
        "consumer_migration_adoption": consumer_migration_adoption(base),
        "agreement_distribution": agreement_distribution(base),
        "divergences_by_classification": divergences_by_classification(base),
        "unresolved_high_risks": unresolved_high_risks(base),
        "interfaces_permanent_count": interfaces_permanent(base),
        "waypoints_at_risk": waypoints_at_risk(base),
    }


def render_text(report):
    lines = ["=== ContextRover Status ===", "", "Stage ledger:"]
    for n in range(9):
        lines.append(f"  Stage {n}: {report['stages'].get(str(n), 'not-started')}")
    lines.append("")

    bsc = report["build_stream_conformity"]
    pct = f"{bsc['percent']:.1f}%" if bsc["percent"] is not None else "unknown"
    lines.append(f"Build Stream conformity:      {pct}  ({bsc['passing']}/{bsc['total']} behaviors passing)")

    cma = report["consumer_migration_adoption"]
    pct2 = f"{cma['percent']:.1f}%" if cma["percent"] is not None else "unknown"
    lines.append(f"Consumer Migration adoption:  {pct2}  ({cma['adopted']}/{cma['total']} interfaces)")
    lines.append("(Reported separately and never blended into one number — REQ-13.)")
    lines.append("")

    lines.append("Ensemble agreement distribution:")
    for k, v in report["agreement_distribution"].items():
        lines.append(f"  found-by-{k}: {v}")
    lines.append("")

    lines.append("Divergences by classification:")
    if report["divergences_by_classification"]:
        for k, v in report["divergences_by_classification"].items():
            lines.append(f"  {k}: {v}")
    else:
        lines.append("  (none recorded)")
    lines.append("")

    risks = report["unresolved_high_risks"]
    lines.append(f"Unresolved high risks: {len(risks)}")
    for r in risks:
        lines.append(f"  [{r.get('id')}] {r.get('statement')}  (blocks: {r.get('blocks_gate')})")
    lines.append("")

    lines.append(
        f"Interfaces with sunset_authority: null (effectively permanent): "
        f"{report['interfaces_permanent_count']}"
    )
    lines.append("")

    at_risk = report["waypoints_at_risk"]
    lines.append(f"Migration Waypoints at-risk or missed: {len(at_risk)}")
    for w in at_risk:
        lines.append(f"  [{w.get('id')}] {w.get('name')} ({w.get('status')}, target {w.get('target_date')}, teams: {', '.join(w.get('teams') or [])})")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dir", default=".contextrover")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    report = build_report(Path(args.dir))
    print(json.dumps(report, indent=2) if args.format == "json" else render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
