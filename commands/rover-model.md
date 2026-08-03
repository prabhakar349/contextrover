---
description: Stage 2 — Strategic Design. K competing boundary proposals plus the operator's own hypothesis; human adjudicates Context boundaries and Divergence classifications.
---

# /rover-model — Stage 2: Strategic Design

Orchestration only (Constitution C9) — Context and Context Map content is defined in `skills/context-model/`, boundary heuristics in `knowledge/ddd-reference.md` §§1, 3–4 (this command loads that reference for the human decision, it does not restate the rules).

## 1. Prerequisites

`state.json` Stage 1 must be `complete`. Read `plugin_root` from `state.json` (set by `/rover-init`) — every plugin-owned path below is `<plugin_root>/<relative-path>`, never bare. Load `charter.md` — fail actionably if absent.

## 2. Dispatch — K competing proposals, plus the operator's own

Dispatch `boundary-proposer` (from `<plugin_root>/stages.json["characterization"]["2"]`, `default_k` passes, varying framing) against the Behavior Inventory, coupling evidence, and event catalogue. Supply `ddd_reference_path: <plugin_root>/knowledge/ddd-reference.md` in its task context — the agent cannot resolve that bare path itself, since its working directory is the target repo, not the plugin. **The operator's own boundary hypothesis is an equal candidate, not a tiebreaker** — collect it before or alongside the agent proposals, not after, so it isn't anchored by them.

## 3. Adjudication — main session, human decider, never a subagent

Present all K+1 candidate boundary sets to the human boundary approver (named at intake, `governance.boundary_approver`). The agent proposes; it never decides (Constitution C9, DR2, and `agents/boundary-proposer.md`'s own explicit constraint). Once the human decides:

- Write `model/contexts.json`, `model/context-map.json` (relationship pattern named for every communicating pair — `knowledge/ddd-reference.md` §1.3). Set each Context's `owning_team` from `intake.json.teams[]` where the human decider names one (extension beyond the base spec pack) — Team Topology (`knowledge/ddd-reference.md` §4 rule 5) is a tiebreaker input to the decision, not something to fill in mechanically after the fact; where the boundary doesn't map cleanly onto an existing team, say so rather than forcing a fit, and leave `owning_team` null.
- Write a Stage-2 Adjudication record (`kind: "adjudication"`, human `decided_by`) for the boundary decision.
- For every Divergence: classify it (`policy` / `false-cognate` / `defect`), and record `decision_owner` + `decided_at` + `rationale` directly on the Divergence record in `inventory/divergences.json` (the divergence record carries its own adjudication trail — `skills/divergence-register/`). For `policy`-classified Divergences, consider whether a `model/variation-policy.json` entry should formalize the variation (`skills/variation-policy/`).

**Failure modes to actively avoid**: letting an agent decide boundaries, settling for "slightly fewer nanoservices" and declaring victory, reconciling a Divergence instead of classifying it.

## 4. Gate

Run `python3 <plugin_root>/scripts/validate-artifacts.py --stage 2 --dir .contextrover` then `python3 <plugin_root>/scripts/trace-lint.py --stage 2 --dir .contextrover`. Both must exit 0: every Behavior maps to exactly one Context; zero `unclassified` Divergences; every Context owns ≥1 aggregate root; the Stage-2 boundary Adjudication record exists.

Append to `gates.jsonl`, commit `.contextrover/`, tag `stage-2-complete`, update `state.json`.
