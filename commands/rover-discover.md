---
description: Stage 1 — Domain Discovery. Unattended K-pass Consensus Run over 9 read-only agents; produces the full Interface, Behavior, Divergence, coupling, sequence, and Redaction Policy inventories.
---

# /rover-discover — Stage 1: Domain Discovery

Orchestration only (Constitution C9) — artifact content and structure are defined in the corresponding skills (`skills/interface-inventory/`, `skills/behavior-inventory/`, `skills/divergence-register/`, etc.), agent extraction behavior in `agents/*.md`, and language-specific discovery patterns in `packs/<language>/PACK.md`. This command selects agents, sets pass order, and enforces the gate.

## 1. Prerequisites

Check `.contextrover/state.json`: Stage 0 must be `complete`. Read `plugin_root` from `state.json` (set by `/rover-init`) — every plugin-owned path below is `<plugin_root>/<relative-path>`, never bare, since this command's working directory is the target repository. Load `charter.md` — fail actionably if absent (never silently default). Read the agent roster for this stage from `<plugin_root>/stages.json["characterization"]["1"]` (v1 ships one `oracle_strategy` key — seam S1.6). If `intake.json.derived.agents_disabled` lists any of these agents as disabled (missing evidence source), skip them and note the resulting gap explicitly rather than silently proceeding as if the roster were complete.

## 2. Dispatch — unattended, K independent passes

Default `k = intake.json.constraints.ensemble_k` (default 3). Each pass uses a distinct framing from `<plugin_root>/stages.json`'s `framings` list (`by-routes`, `by-tests`, `by-call-sites` — D4: vary the vantage point, not the model tier). For each pass, dispatch all 9 discovery agents in parallel, each running under the `discovery-profile` permission profile (read-only, `dontAsk` — Constitution C3: a subagent cannot surface a permission prompt, so this is what lets the pass run unattended with zero approval events).

Each agent's task context must include the resolved absolute path of every plugin file its own prompt tells it to read — an agent cannot resolve `packs/<language>/PACK.md` itself, because its working directory is the target repo, not the plugin (no equivalent of `${CLAUDE_PLUGIN_ROOT}` exists for agent bodies). Concretely, supply `pack_path: <plugin_root>/packs/<language>/PACK.md` (language from `intake.json.estate.source_languages`, one dispatch per language in scope) alongside `framing`. Each agent writes its raw candidates to `.contextrover/passes/1/<framing>/<its-output-file>.json`, per its own prompt — this command does not write agent output itself.

## 3. Consensus aggregation — main session only, deterministic script

**Do not spawn a consensus-runner agent — one must not exist** (Constitution C3, T11: a subagent cannot surface an approval prompt). The union-and-partition step itself is **not** a judgment call the main session improvises — it is deterministic candidate matching (does this by-tests finding describe the same interface as this by-routes finding), exactly the kind of computation Constitution C5 says belongs in one committed, reviewed script. Run:

```
python3 <plugin_root>/scripts/consensus.py --stage 1 --dir .contextrover
```

This reads every framing's raw output under `.contextrover/passes/1/<framing>/`, clusters matching candidates per artifact type (anchor/content matching for Behaviors and Divergences, structural matching for the rest), and writes `.contextrover/consensus/CONSENSUS-<TYPE>.json` (one Consensus Run per artifact type, `kind: "consensus-run"`, `schemas/adjudication.schema.json`, `agreement_rate` computed) plus the merged, deduplicated candidates to `.contextrover/passes/1/merged/<type>.json`. It also assigns stable cross-run IDs for Interfaces and Divergences (REQ-31, using the `IFC_SYNC`/`IFC_ASYNC`/`DVG` counters already reserved in `state.json`) — the same anchor-then-content discipline `scripts/resolve-identity.py` uses for Behaviors, applied here because nothing else does.

For Behaviors specifically: run `python3 <plugin_root>/scripts/resolve-identity.py --candidates .contextrover/passes/1/merged/behaviors.json --dir .contextrover` on `consensus.py`'s merged output to assign stable IDs — **never assign Behavior IDs by agent judgement** (REQ-31a). For other artifact types, `consensus.py`'s merged output already carries stable IDs (Interfaces, Divergences) or needs none (Coupling, Redaction Policy, keyed by their natural fields); accepted candidates become `inventory/{interfaces,divergences,coupling,sequences,redaction-policy}.json` directly.

Present the found-by-one list (and any found-by-some `consensus.json` still marked `"decision": "triage"`) to the operator for review; update those `decision` fields to `accept`/`reject` per their judgment, then assemble `inventory/*.json` from the accepted set only. Write a Stage-1 Adjudication record (`kind: "adjudication"`, human `decided_by`) capturing that review — this is the Stage 1 `[record]` gate criterion.

## 4. Redaction Policy note

A Redaction Policy `NO-GO` does **not** block this stage. It blocks Stage 6 only (REQ-05 correction, `07-stages.md` Stage 1 note). Record it and move on.

## 5. Gate

Run `python3 <plugin_root>/scripts/validate-artifacts.py --stage 1 --dir .contextrover` then `python3 <plugin_root>/scripts/trace-lint.py --stage 1 --dir .contextrover`. Both must exit 0: every Behavior has an ID and ≥1 evidence entry; every async Interface has consumer evidence or explicit `consumers_complete: false`; agreement rate computed; the found-by-one Adjudication record exists.

Run `python3 <plugin_root>/scripts/build-graph.py --dir .contextrover` and `python3 <plugin_root>/scripts/render-report.py --dir .contextrover` to refresh the graph and HTML report (never a gate — a rendering failure is recorded, not fatal, `12-extension-seams.md` §5).

Append to `gates.jsonl`, commit `.contextrover/`, tag `stage-1-complete`, update `state.json`.
