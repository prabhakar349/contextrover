---
description: Stage 7 — Execution (per Slice). Dispatches to the team's existing delivery tooling, runs the frozen harness, and enforces the gate. Does not author the target implementation.
argument-hint: <slice-id>
---

# /rover-execute `<slice-id>` — Stage 7: Execution

Orchestration only (Constitution C9). This command does **not** author target-service code — that is ordinary spec-driven development downstream (`01-spec.md` §4 non-goals). It dispatches to the team's existing tooling, tracks state, runs the harness, enforces the gate, and records the audit trail.

## 1. Harness lock check — first, before anything else

Before any other check: verify `slices/<id>/harness.lock`'s recorded hash still matches the current characterization suite's hash. **If it does not match, fail immediately** and demand a recorded re-approval from the QA/SRE approver before proceeding — do not silently re-freeze the harness or continue past a mismatch. This check runs before the Slice-state prerequisite check below, because a stale lock is the single most likely way a relaxed test would slip through undetected.

## 2. Prerequisites

The named Slice must be `OracleFrozen` (Stage 6 complete, and the lock check above passed). Read `plugin_root` from `state.json` — every plugin-owned path below is `<plugin_root>/<relative-path>`, never bare. Load `charter.md` — fail actionably if absent.

## 3. Dispatch

Hand off to the team's existing implementation tooling for this Slice's target-service changes (ordinary SDD, no extraction or design logic here). Track progress in `slices/<id>/execution-log.jsonl` — each entry a state transition with a timestamp, not free-form narration.

## 4. Gate

Run the harness runner: the full characterization suite must be green, contract tests green, and `python3 <plugin_root>/scripts/run-fitness.py --dir .contextrover --repo .` green — including specifically **no domain logic in adapter packages and no adapter types in domain packages** (`07-stages.md` Stage 7's named failure mode: business logic leaking into adapters recreates two implementations of the same behavior on day one). Run `python3 <plugin_root>/scripts/validate-artifacts.py --stage 7 --dir .contextrover`.

Append to `gates.jsonl`, commit `.contextrover/` (source changes outside `.contextrover/` are committed through the target repository's own normal workflow, not by this command). Update `slices/<id>/slice.json` state to `Accepted` — **this is the Slice's terminal state.** Update `state.json`.
