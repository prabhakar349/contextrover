---
name: cutover-plan
description: Defines the content and structure of a Context's cutover plan — Stage 8 Transition's shadow/canary/cutover/decommission sequencing. Reference when assembling or reviewing contexts/<id>/cutover-plan.json.
---

# Cutover Plan

Defines what a Context's cutover plan contains. Runs per Modeled Context, only once every Slice in that Context has reached `Accepted` — you cannot canary one Slice of a Context whose siblings are unbuilt, because the Context is the deployable boundary (`07-stages.md` §1).

## Schema

`schemas/cutover-plan.schema.json`. A single JSON object per Context — `contexts/<id>/cutover-plan.json` is not an array.

## Required fields

`context`, `transition_profile`, `steps` (≥1).

## Content obligations

- **`transition_profile`** must be set explicitly (seam S1.5) — v1 ships `"shadow-canary-cutover-decommission"`; the Stage 8 command selects a profile rather than hard-coding steps, so a future specification-oracle profile (e.g. direct launch, no legacy shadow) can be added without rework.
- **Steps run in order**: `shadow` (domain logic executes fully, effecting adapters stubbed, decisions diffed) → `canary` → `progressive-cutover` → `decommission`. Each step records its `diff_rate_threshold` and `diff_rate_observed` — the gate is diff rate below threshold at *each* step, not just at the end.
- **`interfaces_retired`** lists every legacy Interface this Context's cutover retires, with `zero_traffic_days` — the Stage 8 gate requires zero traffic for N days before retirement, per Interface, not per Context in aggregate.
- **Sequencing across Contexts** goes by blast radius — read-only and non-effecting Contexts first, state-mutating and externally-effecting Contexts last (`07-stages.md` Stage 8).

## Behavior-ID citation

The cutover plan does not cite Behaviors directly — it operates on Slices (already `Accepted`, already characterized) and Interfaces (already covered by contract tests). Its diffs are behavioral in effect but recorded as `diff-reports/*`, not as new Behavior citations.

## What this skill does not cover

Consumer-facing migration guides and deprecation notices — those belong to the Consumer Migration Workstream (`retirement-register` skill, `/rover-migrate`), which runs in parallel and never gates this plan.

## Minimal worked example

```json
{
  "context": "CTX-0001",
  "transition_profile": "shadow-canary-cutover-decommission",
  "steps": [
    { "name": "shadow", "status": "complete", "diff_rate_threshold": 0.01, "diff_rate_observed": 0.002 },
    { "name": "canary", "status": "in-progress", "diff_rate_threshold": 0.005 }
  ],
  "interfaces_retired": [ { "interface_id": "IFC-SYNC-0001", "zero_traffic_days": 0 } ],
  "decommission_checklist_ref": "contexts/CTX-0001/decommission-checklist.md"
}
```
