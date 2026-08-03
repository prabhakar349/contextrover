#!/usr/bin/env python3
"""Single self-contained HTML program report — scripts/render-report.py.

Writes .contextrover/report/index.html. All CSS/JS/data inlined; no CDN,
no external fonts, no network requests — opens from disk in an air-gapped
environment (Constitution C5, REQ-73). Stdlib only; charts are hand-emitted
inline SVG. Sections per 08-knowledge-and-reporting.md §3.2.

NOT A GATE (12-extension-seams.md §5): this script always exits 0. If
rendering fails, it writes a minimal fallback page recording the failure
instead of raising, so a reporting bug can never block a stage.

Every number carries a `title` attribute naming the artifact file it came
from (hover to see it) — the "traceable to an artifact" design note.
Unknowns render as the literal text "unknown" plus the recorded reason,
never as zero or blank (Constitution C10).

Usage: python3 scripts/render-report.py [--dir .contextrover]
"""
import argparse
import datetime
import html
import json
import subprocess
import sys
import traceback
from pathlib import Path


def load_json(path):
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def esc(value):
    return html.escape(str(value), quote=True)


def unknown_span(reason=None):
    r = f" ({esc(reason)})" if reason else ""
    return f'<span class="unknown">unknown{r}</span>'


def numeric(value, source_file, fmt="{}"):
    return f'<span class="traced" title="{esc(source_file)}">{esc(fmt.format(value))}</span>'


def git_sha(base):
    try:
        out = subprocess.run(
            ["git", "-C", str(base), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------
def collect(base):
    state = load_json(base / "state.json") or {}
    intake = load_json(base / "intake.json") or {}
    behaviors = load_json(base / "inventory" / "behaviors.json") or []
    interfaces = load_json(base / "inventory" / "interfaces.json") or []
    divergences = load_json(base / "inventory" / "divergences.json") or []
    contexts = load_json(base / "model" / "contexts.json") or []
    retirement = load_json(base / "retirement.json") or []

    services = {}
    for b in behaviors:
        for s in b.get("source_services") or []:
            services.setdefault(s, {"behaviors": 0, "sync": 0, "async": 0, "contexts": set()})
            services[s]["behaviors"] += 1
            if b.get("context"):
                services[s]["contexts"].add(b["context"])
    for i in interfaces:
        owner = i.get("owning_service")
        if not owner:
            continue
        services.setdefault(owner, {"behaviors": 0, "sync": 0, "async": 0, "contexts": set()})
        if i.get("kind") == "sync":
            services[owner]["sync"] += 1
        else:
            services[owner]["async"] += 1

    context_state = {c["id"]: c.get("state") for c in contexts if c.get("id")}
    repos = (intake.get("estate") or {}).get("repos") or []
    single_repo = repos[0] if len(repos) == 1 else None
    languages = (intake.get("estate") or {}).get("source_languages") or []

    total_cov = passing_cov = 0
    happy_total = happy_covered = fail_total = fail_covered = 0
    slices_dir = base / "slices"
    if slices_dir.exists():
        for sd in sorted(slices_dir.glob("*")):
            cov = load_json(sd / "verification" / "coverage.json")
            if cov:
                total_cov += cov.get("total", 0)
                passing_cov += cov.get("passing", 0)
                hp = cov.get("happy_path") or {}
                fp = cov.get("failure_path") or {}
                happy_total += hp.get("total", 0)
                happy_covered += hp.get("covered", 0)
                fail_total += fp.get("total", 0)
                fail_covered += fp.get("covered", 0)

    retired_or_zero = sum(1 for r in retirement if r.get("status") in ("zero-traffic", "retired"))
    permanent_count = sum(1 for r in retirement if r.get("sunset_authority") is None)

    agreement_dist = {"all": 0, "some": 0, "one": 0}
    for kind_dir in ("consensus", "adjudications"):
        d = base / kind_dir
        if d.exists():
            for p in sorted(d.glob("*.json")):
                rec = load_json(p)
                if not rec:
                    continue
                for c in rec.get("candidates", []):
                    part = c.get("partition")
                    if part in agreement_dist:
                        agreement_dist[part] += 1

    div_by_class = {}
    for d in divergences:
        c = d.get("classification") or "unclassified"
        div_by_class.setdefault(c, []).append(d)

    approvals = load_json(base / "approvals.json") or []
    risks = (intake.get("derived") or {}).get("risks") or []
    accepted_risk_ids = {
        r["id"] for a in approvals for r in risks if r.get("id") and r["id"] in (a.get("criterion") or "")
    }
    high_risks = [r for r in risks if r.get("severity") == "high" and r.get("id") not in accepted_risk_ids]

    return {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_sha": git_sha(base),
        "state": state,
        "intake": intake,
        "services": services,
        "context_state": context_state,
        "single_repo": single_repo,
        "languages": languages,
        "behaviors": behaviors,
        "interfaces": interfaces,
        "divergences_by_class": div_by_class,
        "retirement": retirement,
        "retired_or_zero": retired_or_zero,
        "permanent_count": permanent_count,
        "coverage": {"total": total_cov, "passing": passing_cov},
        "happy_path": {"total": happy_total, "covered": happy_covered},
        "failure_path": {"total": fail_total, "covered": fail_covered},
        "agreement_dist": agreement_dist,
        "high_risks": high_risks,
        "context_count": len(contexts),
        "stage2_done": (state.get("stages") or {}).get("2", {}).get("status") == "complete",
        "waypoints": load_json(base / "migration-waypoints.json") or [],
    }


# ---------------------------------------------------------------------------
# Inline SVG charts (no external chart library — Constitution C5)
# ---------------------------------------------------------------------------
def svg_gauge(label, pct, source_file):
    if pct is None:
        body = unknown_span("no coverage/retirement data yet")
        bar = f'<rect x="0" y="0" width="200" height="18" fill="#e5e5e5"/>'
    else:
        pct = max(0.0, min(100.0, pct))
        body = numeric(pct, source_file, "{:.1f}%")
        bar = (
            f'<rect x="0" y="0" width="200" height="18" fill="#e5e5e5"/>'
            f'<rect x="0" y="0" width="{pct * 2:.1f}" height="18" fill="#3b6"/>'
        )
    return f'''
    <div class="gauge">
      <div class="gauge-label">{esc(label)}</div>
      <svg width="200" height="18" viewBox="0 0 200 18" role="img" aria-label="{esc(label)}">{bar}</svg>
      <div class="gauge-value">{body}</div>
    </div>'''


def svg_histogram(dist, source_file):
    keys = ["all", "some", "one"]
    values = [dist.get(k, 0) for k in keys]
    maxv = max(values) or 1
    bar_w = 60
    bars = []
    for idx, (k, v) in enumerate(zip(keys, values)):
        h = int((v / maxv) * 80)
        x = idx * (bar_w + 20)
        bars.append(
            f'<rect x="{x}" y="{80 - h}" width="{bar_w}" height="{h}" fill="#369" title="found-by-{k}: {v}"/>'
            f'<text x="{x + bar_w / 2}" y="98" font-size="11" text-anchor="middle">found-by-{k}</text>'
            f'<text x="{x + bar_w / 2}" y="{80 - h - 4 if h else 92}" font-size="11" text-anchor="middle">{v}</text>'
        )
    width = len(keys) * (bar_w + 20)
    return (
        f'<svg width="{width}" height="110" viewBox="0 0 {width} 110" role="img" '
        f'aria-label="Ensemble agreement distribution" title="{esc(source_file)}">{"".join(bars)}</svg>'
    )


# ---------------------------------------------------------------------------
# HTML sections
# ---------------------------------------------------------------------------
def render_header(d):
    n_services = len(d["services"])
    if d["stage2_done"]:
        m = numeric(d["context_count"], "model/contexts.json")
    else:
        m = "M undetermined — Stage 2 pending"
    build_pct = (d["coverage"]["passing"] / d["coverage"]["total"] * 100) if d["coverage"]["total"] else None
    cma_pct = (d["retired_or_zero"] / len(d["retirement"]) * 100) if d["retirement"] else None

    stages_html = []
    for n in range(9):
        status = (d["state"].get("stages") or {}).get(str(n), {}).get("status", "not-started")
        stages_html.append(f'<span class="stage-pill stage-{esc(status)}" title="state.json stages.{n}">S{n}: {esc(status)}</span>')

    sha = d["git_sha"] if d["git_sha"] else unknown_span("no .contextrover git history at render time")

    return f'''
  <section id="header">
    <h1>ContextRover Program Report</h1>
    <p class="meta">Generated {esc(d["generated_at"])} · .contextrover git SHA: {sha}
       · <em>current as of the last gate, not live</em></p>
    <p class="headline">{numeric(n_services, "inventory/behaviors.json + inventory/interfaces.json")}
       services in &rarr; {m} proposed out</p>
    <div class="stage-rail">{"".join(stages_html)}</div>
    <div class="gauges">
      {svg_gauge("Build Stream conformity", build_pct, "slices/*/verification/coverage.json")}
      {svg_gauge("Consumer Migration adoption", cma_pct, "retirement.json")}
    </div>
    <p class="note">These two gauges are reported separately and never blended into one number (REQ-13).</p>
  </section>'''


def render_services(d):
    rows = []
    for name, info in sorted(d["services"].items()):
        if d["single_repo"]:
            repo_cell = f'<a href="{esc(d["single_repo"])}">{esc(d["single_repo"])}</a>'
        else:
            repo_cell = unknown_span("no unambiguous per-service repository mapping in intake.json estate.repos")
        ctx_ids = sorted(info["contexts"])
        if ctx_ids:
            ctx_cell = ", ".join(esc(c) for c in ctx_ids)
        else:
            ctx_cell = unknown_span("no Behavior from this service has been mapped to a Context yet")
        rows.append(
            "<tr>"
            f"<td>{esc(name)}</td>"
            f"<td>{esc(', '.join(d['languages']) or 'unknown')}</td>"
            f"<td>{repo_cell}</td>"
            f"<td>{numeric(info['sync'], 'inventory/interfaces.json')}</td>"
            f"<td>{numeric(info['async'], 'inventory/interfaces.json')}</td>"
            f"<td>{numeric(info['behaviors'], 'inventory/behaviors.json')}</td>"
            f"<td>{ctx_cell}</td>"
            "</tr>"
        )
    return f'''
  <section id="services">
    <h2>Service inventory</h2>
    <input class="filter" type="text" placeholder="Filter services..." data-table="services-table">
    <table id="services-table">
      <thead><tr>
        <th data-sort="text">Service</th><th data-sort="text">Language</th><th data-sort="text">Repository</th>
        <th data-sort="num">Sync IFCs</th><th data-sort="num">Async IFCs</th><th data-sort="num">Behaviors</th>
        <th data-sort="text">Proposed context</th>
      </tr></thead>
      <tbody>{"".join(rows) if rows else "<tr><td colspan=7>(no services discovered yet)</td></tr>"}</tbody>
    </table>
  </section>'''


def render_stage_timeline(d):
    rows = []
    for n in range(9):
        s = (d["state"].get("stages") or {}).get(str(n), {})
        status = s.get("status", "not-started")
        gate = s.get("gate_result") or {}
        gate_cell = (
            f"exit {numeric(gate.get('exit_code'), 'gates.jsonl')} ({esc(gate.get('script', ''))})"
            if gate else unknown_span("no gate run recorded yet")
        )
        rows.append(
            "<tr>"
            f"<td>Stage {n}</td><td>{esc(status)}</td>"
            f"<td>{esc(s.get('started_at') or '—')}</td><td>{esc(s.get('completed_at') or '—')}</td>"
            f"<td>{gate_cell}</td>"
            f"<td>{numeric(len(s.get('artifacts') or []), 'state.json')}</td>"
            f"<td>{esc(s.get('operator') or 'unknown')}</td>"
            "</tr>"
        )
    return f'''
  <section id="timeline">
    <h2>Stage timeline</h2>
    <table>
      <thead><tr><th>Stage</th><th>Status</th><th>Started</th><th>Completed</th>
        <th>Gate result</th><th>Artifacts</th><th>Operator</th></tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table>
  </section>'''


def render_coverage(d):
    cov = d["coverage"]
    happy = d["happy_path"]
    fail = d["failure_path"]
    return f'''
  <section id="coverage">
    <h2>Coverage</h2>
    <p>Behaviors: {numeric(cov["passing"], "slices/*/verification/coverage.json")} passing of
       {numeric(cov["total"], "slices/*/verification/coverage.json")} covered.</p>
    <p>Happy-path: {numeric(happy["covered"], "slices/*/verification/coverage.json")} /
       {numeric(happy["total"], "slices/*/verification/coverage.json")}
       &nbsp;·&nbsp; Failure-path: {numeric(fail["covered"], "slices/*/verification/coverage.json")} /
       {numeric(fail["total"], "slices/*/verification/coverage.json")}
       <span class="note">(reported separately — a suite complete only on happy paths is the characteristic silent failure)</span></p>
    <h3>Ensemble agreement distribution</h3>
    {svg_histogram(d["agreement_dist"], "consensus/*.json + adjudications/*.json")}
  </section>'''


def render_divergences(d):
    order = ["unclassified", "policy", "false-cognate", "defect"]
    blocks = []
    for cls in order:
        items = d["divergences_by_class"].get(cls, [])
        css = "class-unclassified" if cls == "unclassified" else ""
        rows = []
        for item in items:
            owner = esc(item.get("decision_owner")) if item.get("decision_owner") else unknown_span("no decision_owner recorded")
            proj = item.get("projection") or {}
            link = f'<a href="{esc(proj.get("external_id"))}">{esc(proj.get("external_id"))}</a>' if proj.get("status") == "projected" else "—"
            rows.append(f"<tr><td>{esc(item.get('id'))}</td><td>{esc(item.get('concept'))}</td><td>{owner}</td><td>{link}</td></tr>")
        blocks.append(
            f'<h3 class="{css}">{esc(cls)} ({numeric(len(items), "inventory/divergences.json")})</h3>'
            f'<table><thead><tr><th>ID</th><th>Concept</th><th>Decision owner</th><th>Tracked issue</th></tr></thead>'
            f'<tbody>{"".join(rows) if rows else "<tr><td colspan=4>(none)</td></tr>"}</tbody></table>'
        )
    return f'<section id="divergences"><h2>Divergences</h2>{"".join(blocks)}</section>'


def render_risks(d):
    rows = [
        f"<tr><td>{esc(r.get('id'))}</td><td>{esc(r.get('statement'))}</td><td>{esc(r.get('blocks_gate') or '—')}</td></tr>"
        for r in d["high_risks"]
    ]
    return f'''
  <section id="risks">
    <h2>Risks</h2>
    <p>Unresolved high risks: {numeric(len(d["high_risks"]), "intake.json")}</p>
    <table><thead><tr><th>ID</th><th>Statement</th><th>Blocks gate</th></tr></thead>
      <tbody>{"".join(rows) if rows else "<tr><td colspan=3>(none)</td></tr>"}</tbody></table>
    <p class="note">Interfaces with sunset_authority: null (effectively permanent):
      {numeric(d["permanent_count"], "retirement.json")} — the leading indicator the
      Consumer Migration Stream will never finish.</p>
  </section>'''


def render_waypoints(d):
    """Extension beyond the base spec pack: Migration Waypoints, team-attributable deadlines
    on top of the Retirement Register's per-interface status."""
    rows = []
    for w in d["waypoints"]:
        css = "class-unclassified" if w.get("status") in ("at-risk", "missed") else ""
        rows.append(
            f"<tr class=\"{css}\"><td>{esc(w.get('id'))}</td><td>{esc(w.get('name'))}</td>"
            f"<td>{esc(w.get('target_date'))}</td><td>{esc(', '.join(w.get('teams') or []))}</td>"
            f"<td>{esc(', '.join(w.get('interfaces') or []))}</td><td>{esc(w.get('status'))}</td></tr>"
        )
    at_risk_count = sum(1 for w in d["waypoints"] if w.get("status") in ("at-risk", "missed"))
    return f'''
  <section id="waypoints">
    <h2>Migration Waypoints</h2>
    <p class="note">Extension beyond the base spec pack — dated, team-attributable checkpoints on top of the Retirement Register.</p>
    <p>At-risk or missed: {numeric(at_risk_count, "migration-waypoints.json")}</p>
    <table><thead><tr><th>ID</th><th>Name</th><th>Target date</th><th>Teams</th><th>Interfaces</th><th>Status</th></tr></thead>
      <tbody>{"".join(rows) if rows else "<tr><td colspan=6>(none recorded)</td></tr>"}</tbody></table>
  </section>'''


def render_retirement(d):
    rows = []
    for r in d["retirement"]:
        rows.append(
            "<tr>"
            f"<td>{esc(r.get('interface_id'))}</td>"
            f"<td>{esc(', '.join(r.get('known_consumers') or []) or 'none recorded')}</td>"
            f"<td>{esc(r.get('status'))}</td>"
            f"<td>{esc(r.get('sunset_date') or '—')}</td>"
            f"<td>{esc(r.get('sunset_authority')) if r.get('sunset_authority') else unknown_span('permanent — no sunset authority named')}</td>"
            f"<td>{esc(r.get('last_traffic') or '—')}</td>"
            f"<td>{esc(r.get('zero_traffic_days')) if r.get('zero_traffic_days') is not None else '—'}</td>"
            "</tr>"
        )
    return f'''
  <section id="retirement">
    <h2>Retirement register</h2>
    <table>
      <thead><tr><th>Interface</th><th>Known consumers</th><th>Status</th><th>Sunset date</th>
        <th>Sunset authority</th><th>Last traffic</th><th>Zero-traffic days</th></tr></thead>
      <tbody>{"".join(rows) if rows else "<tr><td colspan=7>(no legacy interfaces tracked yet)</td></tr>"}</tbody>
    </table>
  </section>'''


CSS = '''
body { font-family: -apple-system, "Segoe UI", Arial, sans-serif; margin: 2rem; color: #111; line-height: 1.5; }
h1 { margin-bottom: 0.2rem; }
.meta { color: #666; font-size: 0.85rem; }
.headline { font-size: 1.1rem; }
section { margin-bottom: 2.5rem; }
table { border-collapse: collapse; width: 100%; margin-top: 0.5rem; }
th, td { border: 1px solid #ccc; padding: 0.4rem 0.6rem; text-align: left; font-size: 0.9rem; }
th { background: #f0f0f0; cursor: pointer; }
.unknown { color: #a55; font-style: italic; }
.traced { border-bottom: 1px dotted #999; cursor: help; }
.note { color: #666; font-size: 0.85rem; }
.stage-rail { display: flex; gap: 0.3rem; flex-wrap: wrap; margin: 0.8rem 0; }
.stage-pill { padding: 0.2rem 0.5rem; border-radius: 4px; background: #eee; font-size: 0.8rem; }
.stage-complete { background: #cfc; }
.stage-in-progress { background: #ffe; }
.stage-gate-failed { background: #fcc; }
.gauges { display: flex; gap: 2rem; margin-top: 1rem; }
.gauge-label { font-size: 0.85rem; margin-bottom: 0.2rem; }
.gauge-value { font-size: 0.85rem; margin-top: 0.2rem; }
.class-unclassified { color: #c00; }
.filter { margin: 0.5rem 0; padding: 0.3rem; width: 100%; max-width: 20rem; }
@media print { body { margin: 0.5in; } .filter { display: none; } }
'''

JS = '''
document.querySelectorAll("input.filter").forEach(function (input) {
  var table = document.getElementById(input.dataset.table);
  if (!table) return;
  input.addEventListener("input", function () {
    var q = input.value.toLowerCase();
    table.querySelectorAll("tbody tr").forEach(function (row) {
      row.style.display = row.textContent.toLowerCase().indexOf(q) === -1 ? "none" : "";
    });
  });
});
document.querySelectorAll("table thead th[data-sort]").forEach(function (th, idx) {
  th.addEventListener("click", function () {
    var table = th.closest("table");
    var tbody = table.querySelector("tbody");
    var rows = Array.prototype.slice.call(tbody.querySelectorAll("tr"));
    var kind = th.dataset.sort;
    var asc = th.dataset.asc !== "true";
    th.dataset.asc = asc;
    rows.sort(function (a, b) {
      var av = a.children[idx].textContent.trim();
      var bv = b.children[idx].textContent.trim();
      if (kind === "num") { av = parseFloat(av) || 0; bv = parseFloat(bv) || 0; return asc ? av - bv : bv - av; }
      return asc ? av.localeCompare(bv) : bv.localeCompare(av);
    });
    rows.forEach(function (r) { tbody.appendChild(r); });
  });
});
'''


def render(base):
    d = collect(base)
    body = "\n".join([
        render_header(d),
        render_services(d),
        render_stage_timeline(d),
        render_coverage(d),
        render_divergences(d),
        render_risks(d),
        render_waypoints(d),
        render_retirement(d),
    ])
    data_blob = json.dumps(
        {k: v for k, v in d.items() if k not in ("services", "context_state")}, default=str, indent=2
    )
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>ContextRover Program Report</title>
<style>{CSS}</style>
</head>
<body>
{body}
<script type="application/json" id="report-data">{data_blob}</script>
<script>{JS}</script>
</body>
</html>
'''


def fallback_html(error_text):
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>ContextRover Program Report — generation failed</title></head>
<body>
<h1>ContextRover Program Report</h1>
<p><strong>Report generation failed.</strong> This is not a gate (12-extension-seams.md §5) —
the failure is recorded here rather than blocking the stage.</p>
<pre>{html.escape(error_text)}</pre>
</body></html>
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dir", default=".contextrover")
    args = parser.parse_args()

    base = Path(args.dir)
    out_dir = base / "report"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "index.html"

    try:
        content = render(base)
        out_path.write_text(content)
        print(f"OK: wrote {out_path}")
    except Exception:
        err = traceback.format_exc()
        print(f"WARNING: report generation failed, writing fallback page:\n{err}", file=sys.stderr)
        out_path.write_text(fallback_html(err))

    return 0  # never a gate — always exit 0


if __name__ == "__main__":
    sys.exit(main())
