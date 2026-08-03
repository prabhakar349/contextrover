---
description: Stage 6 — Verification Design (per Slice). Adversarial generator/test-adversary loop builds the characterization suite, contract tests, and fitness functions, then freezes the harness.
argument-hint: <slice-id>
---

# /rover-verify `<slice-id>` — Stage 6: Verification Design

Orchestration only (Constitution C9) — suite content is defined in `skills/characterization-suite/`, `skills/contract-tests/`, `skills/observability-spec/`; harness conventions come from `packs/<language>/PACK.md` (Constitution C8 — this is one of the three stages allowed to consult a pack).

## 1. Prerequisites

The named Slice must be `Designed` (Stage 5 complete). Read `plugin_root` from `state.json` — every plugin-owned path below is `<plugin_root>/<relative-path>`, never bare. Load `charter.md` — fail actionably if absent.

## 2. Redaction Policy gate — checked here, not at Stage 1

For every Interface this Slice's Behaviors touch, `inventory/redaction-policy.json` must show `verdict: "GO"`. A `NO-GO` here blocks this stage specifically (REQ-05 correction) — resolve the masking approach or escalate before continuing.

## 3. Adversarial build

Generate the characterization suite at the **protocol boundary** (HTTP/event payloads, never language internals — DR1): happy paths, failure paths, timeouts, partial completion, and event emission (which events, what order, what partition keys). Generate consumer-driven contract tests and architecture fitness functions (adapter/domain separation, per `<plugin_root>/packs/<language>/PACK.md`'s `fitness.json`). Generate the observability spec.

Dispatch `test-adversary` (from `<plugin_root>/stages.json["characterization"]["6"]`) against the draft suite — it probes failure paths, timeouts, partial completion, and event ordering specifically. Iterate until its findings are addressed or explicitly accepted.

Run `python3 <plugin_root>/scripts/run-fitness.py --dir .contextrover --repo .` against the **existing system** (the script resolves `packs/<language>/fitness.json` relative to its own installed location automatically — no `--pack-dir` override needed once it is invoked via its full `<plugin_root>` path) — every fitness function must pass against what already exists. A fitness function that fails against the system you already have is a wrong function, not a finding (`07-stages.md` Stage 6 note); fix the function, not the system.

## 4. Freeze the harness

Once the suite, contracts, and fitness functions are accepted: compute the suite's hash and write it to `slices/<id>/harness.lock`. **This is the mechanism behind "the target moved, the scoreboard didn't"** — without the lock the claim is unenforced. It is not optional.

## 5. Gate

Run `python3 <plugin_root>/scripts/validate-artifacts.py --stage 6 --dir .contextrover` then `python3 <plugin_root>/scripts/trace-lint.py --stage 6 --dir .contextrover`. Both must exit 0: Redaction Policy verdict GO for every Interface in this Slice; characterization coverage of this Slice's Behaviors at or above threshold; failure-path Behaviors covered, reported separately; `harness.lock` written.

Append to `gates.jsonl`, commit `.contextrover/`, update `slices/<id>/slice.json` state to `OracleFrozen`, update `state.json`.
