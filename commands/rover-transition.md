---
description: Stage 8 — Transition (per Modeled Context). Shadow, canary, progressive cutover, and decommission, once every Slice in the Context is Accepted.
argument-hint: <context-id>
---

# /rover-transition `<context-id>` — Stage 8: Transition

Orchestration only (Constitution C9) — Cutover Plan content is defined in `skills/cutover-plan/`. No agent is dispatched for this stage.

## 1. Prerequisites

**Every Slice in this Context must be `Accepted`.** You cannot canary one Slice of a Context whose siblings are unbuilt — the Context is the deployable boundary, not the Slice (`07-stages.md` Stage 8 rationale). Read `plugin_root` from `state.json` — every plugin-owned path below is `<plugin_root>/<relative-path>`, never bare. Load `charter.md` — fail actionably if absent.

## 2. Sequencing

Where multiple Contexts are ready for Transition, sequence by blast radius: read-only and non-effecting Contexts first, state-mutating and externally-effecting Contexts last.

## 3. Run the cutover

Write or update `contexts/<id>/cutover-plan.json` with `transition_profile: "shadow-canary-cutover-decommission"` (seam S1.5 — v1's only profile). Step through: **shadow** (domain logic executes fully, effecting adapters stubbed, decisions diffed against the legacy system — write `diff-reports/*`), **canary**, **progressive-cutover**, **decommission**. At each step, diff rate must stay below its configured threshold and SLO gates must hold — checked by `python3 <plugin_root>/scripts/status-report.py --dir .contextrover`, not `trace-lint.py`, since this is operational health, not traceability.

In parallel, the Consumer Migration Workstream (`/rover-migrate`) retires legacy Interfaces this Context owns — **it never gates this stage**, do not wait on it.

## 4. Decommission — `[record]`

Before marking a superseded service decommissioned, write `contexts/<id>/decommission-checklist.md` and record a human Approval for it: append to `.contextrover/approvals.json` with `artifact: "contexts/<id>/decommission-checklist.md"` and `version_hash` matching the checklist's current sha256.

Per Interface being retired: confirm zero traffic for the required number of days before actually retiring it in `retirement.json` — update `retirement.json` here as interfaces cross that threshold.

## 5. Gate

Run `python3 <plugin_root>/scripts/status-report.py --dir .contextrover` for the diff-rate/SLO checks and `python3 <plugin_root>/scripts/trace-lint.py --stage 8 --dir .contextrover` for the decommission Approval record check. Both must pass: diff rate below threshold at each step; SLO gates hold; superseded services decommissioned with a recorded Approval; per Interface, zero traffic for the required days before retirement.

Append to `gates.jsonl`, commit `.contextrover/`, update the Context's state in `state.json` through `Shadowing → Canary → Cutover → Decommissioned` as each step completes, tag `stage-8-<context-id>-complete` on final decommission.
