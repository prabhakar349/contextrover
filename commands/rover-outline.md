---
description: Stage 3 — Solution Outline. Partitions Behaviors into Slices; drafts PRD, acceptance criteria, test approach, and size per Slice.
---

# /rover-outline — Stage 3: Solution Outline

Orchestration only (Constitution C9) — Slice, Size, and Acceptance Criteria content is defined in `skills/slice-outline/`, `skills/acceptance-criteria/`, and `skills/design-doc/` (for the PRD's citation obligations), not here. No agent is dispatched for this stage (`02-plan.md` §5 stage-to-component map) — drafting happens directly in the main session, reviewed by product and tech leads.

## 1. Prerequisites

`state.json` Stage 2 must be `complete`. Read `plugin_root` from `state.json` — every plugin-owned path below is `<plugin_root>/<relative-path>`, never bare. Load `charter.md` — fail actionably if absent.

## 2. Partition and draft

Partition the approved Contexts' Behaviors into Slices — every Behavior assigned to exactly one Slice. Create `workstreams.json`: one context-scoped Workstream per Context with Slices, plus the cross-cutting Walking Skeleton workstream (Increment 0's content — infra, data stores, pipeline, observability, monitoring, security, exercised end to end) and the Consumer Migration Workstream (owned by the Engagement directly, not by any Context — `07-stages.md` §4).

For each Slice: draft `slices/<id>/{prd.md, acceptance-criteria.json, test-approach.md, size.json}`. `size.json` contains no dates — dates belong only to Stage 4. Write `slices/<id>/slice.json` (the Slice record itself, `schemas/slice.schema.json`) with `state: "Outlined"` and `oracle_strategy: "characterization"` (v1 accepts no other value — seam S1.1).

## 3. Review

Product and tech lead review each Slice's PRD and acceptance criteria before the gate. No Slice may exceed the configured maximum size (`trace-lint.py`'s `max_slice_work_units` seed, overridable via `state.json.gate_config` — `07-stages.md` Stage 3 note) — oversized Slices must be split here, before roadmapping, not discovered as a problem in Stage 4.

## 4. Gate

Run `python3 <plugin_root>/scripts/validate-artifacts.py --stage 3 --dir .contextrover` then `python3 <plugin_root>/scripts/trace-lint.py --stage 3 --dir .contextrover`. Both must exit 0: every Behavior assigned to exactly one Slice; every Slice has acceptance criteria and a `size.json`; no Slice over max size; `oracle_strategy == "characterization"` for every Slice.

Append to `gates.jsonl`, commit `.contextrover/`, tag `stage-3-complete`, update `state.json`.
