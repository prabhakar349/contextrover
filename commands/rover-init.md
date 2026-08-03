---
description: Stage 0 — Engagement Intake. Runs the six-section interview, probes connector availability, computes derived risks, and initializes .contextrover/ as its own git repository.
---

# /rover-init — Stage 0: Engagement Intake

Orchestration only (Constitution C9) — this command selects steps and enforces the gate; the intake's actual content and structure are defined in `06-intake.md`, not here.

## 0. Resolve and record the plugin's own install path (before anything else)

Every command's working directory is the target repository, not the plugin's own install location — Claude Code exposes `${CLAUDE_PLUGIN_ROOT}` to hooks and `${CLAUDE_SKILL_DIR}` to skills, but neither exists for command or agent markdown bodies. Without an absolute path recorded once, no later step can reliably reach the plugin's own `schemas/`, `packs/`, `knowledge/`, `scripts/`, `charter.template.md`, or `stages.json` — including this command's own next step.

If `.contextrover/state.json` already has a `plugin_root` value, verify it still points at a real contextrover install (`<plugin_root>/.claude-plugin/plugin.json` exists and its `name` is `"contextrover"`) and skip the rest of this step silently if so.

Otherwise, ask the operator directly: *"What is the absolute filesystem path where the contextrover plugin is installed?"* Verify the answer the same way (the plugin manifest must exist and name itself `contextrover`) — if verification fails, say so plainly and ask again rather than guessing or proceeding on an unverified path. Once verified, write it to `.contextrover/state.json` as `plugin_root` (`schemas/state.schema.json`). This happens once per engagement.

Every step below, and every command after this one, reads `plugin_root` from `state.json` and resolves plugin-owned files as `<plugin_root>/<relative-path>` — never as a bare relative path.

## 1. Charter check

If `charter.md` does not exist in the target repository root: copy `<plugin_root>/charter.template.md` to `charter.md`, and **stop immediately** with instructions to fill it in and re-run `/rover-init`. Do not proceed with intake on a missing charter (REQ-71). `charter.md` must already be listed in `.gitignore` — if it is not, add it before stopping.

If `charter.md` exists: check it for placeholder tokens (anything still matching the template's commented placeholder markers). If any remain, fail actionably, naming which section still has a placeholder, and stop. A placeholder charter must never silently pass (Constitution C4).

## 2. Run the six-section intake

Follow `06-intake.md` exactly: sections A (Estate), B (Evidence sources), C (Constraints), D (Integrations — capability probe), E (Governance), F (Delivery Capacity). One question at a time (P1). If `.contextrover/intake.json` already exists, this is a re-entry — pre-fill and confirm existing answers rather than re-asking (P4). `unknown` is a legitimate answer for any question (P3).

For Section D specifically, follow the capability probe protocol in `06-intake.md` §3 precisely: **probe MCP tool availability before asking any system-specific configuration question.** Never ask for a project key, space name, or similar configuration for a connector that the probe found unavailable (P2). Adapter specs are in `adapters/`.

## 3. Section G — Teams and delivery mechanism (extension beyond `06-intake.md`)

Not part of the base spec pack's six sections — added so boundary decisions and migration waypoints have a real team roster to reference instead of free text invented later. Same conversational discipline as the rest of intake (P1 one question at a time; P3 `unknown` is legitimate; P4 pre-fill on re-entry).

- **Team roster**: for each team in scope, name and which services it currently owns in the source estate (`intake.json.teams[]`). This is a roster of *today's* ownership, not a target-state assignment — Stage 2 may draw Context boundaries that don't match it, and that mismatch is itself boundary evidence (Team Topology, `knowledge/ddd-reference.md` §4 rule 5), not an error to correct at intake.
- **Delivery mechanism** (`intake.json.delivery_mechanism`): how this org actually ships — continuous deployment, a release train, a manual gate, or something else (`model`), plus a short free-text description of the environment promotion path and who gates what. Distinct from Section F's numeric capacity answers (deploys/week, CI cycle time) — this is the *shape* of the process, not its throughput, and Stage 4/8 use it to sequence realistically rather than assume every org ships the same way.

## 4. Compute the derived block

`intake.json.derived` (agents enabled/disabled, packs loaded, risks) is computed from the answers per the fixed rules in `06-intake.md` §5 — apply them exactly, do not improvise new risk conditions. (Section G answers are not inputs to these fixed rules — they are not part of the base spec pack's risk model.)

## 5. Initialize the artifact repository

If `.contextrover/` does not yet have its own git history, run `git init` inside it, write its `.gitignore`, and make the initial commit (`08-knowledge-and-reporting.md` §2, T11c). This is a separate repository from the target estate's own git history — document this to the operator since a nested `.git` surprises people.

## 6. Gate

Write `intake.json`. Run `python3 <plugin_root>/scripts/validate-artifacts.py --stage 0 --dir .contextrover`. Gate passes when: intake is schema-valid, `charter.md` is present with no placeholder tokens, and every high risk from the derived block is either resolved or explicitly accepted by the operator with a recorded rationale (do not silently pass an unresolved high risk).

Append the gate result to `.contextrover/gates.jsonl`. Update `.contextrover/state.json` stage 0 to `complete`. Commit `.contextrover/` with the message convention from `08-knowledge-and-reporting.md` §2, and tag `stage-0-complete`.

## 7. Report to the operator

Print, per `06-intake.md` §6: which agents will run in Stage 1 and which are disabled and why; which language packs will load; which adapters are ready, unavailable, or disabled; the high-risk list; and the single recommended first action (usually reframing the success metric if E1 is unresolved — E1/E2 together are the political early-warning system, `06-intake.md` §2 section E).
