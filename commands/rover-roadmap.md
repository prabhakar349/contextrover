---
description: Stage 4 — Delivery Roadmap. Turns Slice sizes into a capacity-constrained, confidence-banded forecast, with Increment 0 always the Walking Skeleton.
---

# /rover-roadmap — Stage 4: Delivery Roadmap

Orchestration only (Constitution C9) — Roadmap content is defined in `skills/roadmap/`, the estimation model in `11-estimation.md` (implemented once in the capacity computation, not restated here). No agent is dispatched for this stage.

## 1. Prerequisites

`state.json` Stage 3 must be `complete` for every Slice being roadmapped. Read `plugin_root` from `state.json` — every plugin-owned path below is `<plugin_root>/<relative-path>`, never bare. Load `charter.md` — fail actionably if absent.

## 2. Compute capacity and sequence

Apply `11-estimation.md`'s model exactly: `work_units` per Slice from `size.json`, `estimated_prs`, then `throughput = min(authoring_rate, review_rate, integration_rate)` with the binding constraint named explicitly. Use `intake.json` §F capacity answers; every default used because an answer was `unknown` goes into `roadmap.json.capacity.assumptions_used` — never a silent default.

**Increment 0 is always the Walking Skeleton.** Nothing precedes it. Sequence the rest by dependency and blast radius, then defer to the business priority leadership supplies — **flag conflicts, never override either side silently** (`priority_conflicts`).

Confidence band derives from the Stage 1 agreement rate (`11-estimation.md` §5): ≥0.90 → ±20%, 0.75–0.90 → ±40%, <0.75 → ±80% **and** a prominent recommendation to extend Discovery rather than commit to a date on poorly understood scope.

## 3. Leadership approval — `[record]`

This is a human-shaped artifact: present the draft roadmap, its binding constraint, and its sensitivity table (effect of +1 reviewer, +1 engineer, +1 deploy/week, −1 day approval latency) to leadership. Once approved, write an Approval record (`schemas/approval.schema.json`) to `.contextrover/approvals.json` with `artifact: "roadmap.json"`, `version_hash` set to the roadmap file's current sha256, and `decided_by` a named human. This binds the approval to this exact version — any later edit voids it and requires re-approval.

## 4. Gate

Write `roadmap.json`. Run `python3 <plugin_root>/scripts/validate-artifacts.py --stage 4 --dir .contextrover` then `python3 <plugin_root>/scripts/trace-lint.py --stage 4 --dir .contextrover`. Both must exit 0: every Slice appears exactly once; Increment 0 is the Walking Skeleton; every Increment has a named owner; the capacity model names its binding constraint; the leadership Approval record exists and matches the roadmap's current hash.

Append to `gates.jsonl`, commit `.contextrover/`, tag `stage-4-complete`, update `state.json`. **Re-forecast is mandatory after Increment 0 completes** — note this obligation to the operator now.
