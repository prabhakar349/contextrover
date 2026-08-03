---
description: Stage 5 — Tactical Design (per Slice, just-in-time). Aggregates, invariants, domain events, commands, policies, API/event contracts, and legacy adapter specs for one Slice.
argument-hint: <slice-id>
---

# /rover-design `<slice-id>` — Stage 5: Tactical Design

Orchestration only (Constitution C9) — Tactical Model and ADR content is defined in `skills/tactical-model/`, `skills/design-doc/`, `skills/adr/`; DDD grounding in `knowledge/ddd-reference.md` §2 (aggregate rules), loaded for this design work, not restated here.

## 1. Prerequisites

The named Slice must exist (`state.json`) with its Context `Approved` (Stage 2 complete) and appear in the current `roadmap.json` (Stage 4 complete). Read `plugin_root` from `state.json` — every plugin-owned path below is `<plugin_root>/<relative-path>`, never bare. Load `charter.md` — fail actionably if absent. Designed **just-in-time** — do not design every Slice up front; that is waterfall and discards what earlier Slices already taught (`07-stages.md` Stage 5 rationale).

## 2. Draft and critique

Draft `slices/<id>/{tactical-model.json, design.md, api/*.yaml, events/*.json, adapters/*.md}` and any needed `adr/*.md`. Dispatch `spec-critic` (from `<plugin_root>/stages.json["characterization"]["5"]`) against the draft — ambiguity, missing error cases, unstated assumptions, uncited clauses. Supply `ddd_reference_path: <plugin_root>/knowledge/ddd-reference.md` in its task context — the agent cannot resolve that bare path itself. Iterate until the critic's findings are addressed or explicitly accepted with rationale.

Every aggregate needs ≥1 real invariant (Vernon's rule 1, `knowledge/ddd-reference.md` §2.1) — not a data bag. Every legacy Interface in scope needs a named adapter owner (Anticorruption Layer by default for legacy integration).

## 3. Architecture review — `[record]`

Human architecture review must explicitly cover the judgment criterion: *no invariant requires a synchronous call to a sibling aggregate*. Once approved, append an Approval record to `slices/<id>/slice.json`'s `approvals[]` array, with `version_hash` set to `tactical-model.json`'s current sha256 and `decided_by` a named human.

## 4. Gate

Run `python3 <plugin_root>/scripts/validate-artifacts.py --stage 5 --dir .contextrover` then `python3 <plugin_root>/scripts/trace-lint.py --stage 5 --dir .contextrover`. Both must exit 0: every aggregate declares ≥1 invariant; every design clause cites a Behavior ID; no orphan Behavior IDs in this Slice; every legacy Interface in scope has a named adapter owner; the architecture-review Approval record exists and matches the current hash.

Append to `gates.jsonl`, commit `.contextrover/`, update `slices/<id>/slice.json` state to `Designed`, update `state.json`.
