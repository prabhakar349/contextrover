# Build Report — contextrover v1

Final review per T21: `00-constitution.md` re-read against the built repository, principle by principle, with evidence. Followed by the seam checklist (`12-extension-seams.md` §6, verified at T20) and every accepted deviation made during the build, with rationale.

---

## Post-T21 extension: team ownership, delivery mechanism, and migration waypoints

User-requested, **explicitly beyond the base spec pack** (`01-spec.md`/`07-stages.md` name none of this) — not something the original specs asked for, and not represented as if they did. Three additions, all user-scoped via explicit questions before building:

1. **`context.schema.json` gains `owning_team`.** Team Topology is already named as a boundary heuristic (`knowledge/ddd-reference.md` §4 rule 5, a tiebreaker, never primary), but nothing recorded who actually owns a Context once decided. `rover-model.md` now sets it from the intake team roster during Stage 2 adjudication — never mechanically, since a boundary may legitimately not map onto an existing team.
2. **`intake.schema.json` gains `teams[]` and `delivery_mechanism`.** A new "Section G" in `rover-init.md`, explicitly marked as an extension beyond `06-intake.md`'s six sections — a team roster (name, services currently owned, lead) and the org's actual release process shape (continuous / release-train / manual-gate + free text), distinct from Section F's numeric capacity answers. Section G answers are not inputs to `06-intake.md` §5's fixed derived-risk rules.
3. **New `waypoint.schema.json` / `migration-waypoints.json`**, driven by `rover-migrate.md`. Dated, team-attributable checkpoints on top of the Retirement Register's per-interface status — a Waypoint names which team(s) must have migrated off which legacy Interfaces by when, with the same evidence-gated status discipline (`pending → at-risk/met/missed`) `retirement.json` already uses. Surfaced prominently by `status-report.py` (`waypoints_at_risk`) and `render-report.py` (a dedicated section), alongside the existing `sunset_authority: null` signal.

Wired through fully, not just documented: `state.schema.json` gains a `WP` counter and `plugin_root`'s sibling; `validate-artifacts.py` maps the new artifact; a new skill (`skills/migration-waypoints/`) documents the artifact per the established content/structure convention. Proven against `fixtures/sample-estate/` — a full team roster, `delivery_mechanism`, `owning_team` on all three Contexts, and two waypoints (one `pending`, one deliberately seeded `at-risk`) were added, and `validate-artifacts.py` (36 files), `trace-lint.py` (Stages 1–4), `status-report.py`, and `render-report.py` were all re-run and confirmed to surface the at-risk waypoint correctly end to end.

---

## Post-T21 critical review: three bugs found and fixed by actually running the pipeline

A user-requested critical review after T21 surfaced that T19's fixture had bypassed the one piece of orchestration logic Stage 1's ensemble design depends on: the K-pass consensus/dedup step. `rover-discover.md` described it as prose ("union… partition…") with no deterministic script behind it — a real gap, not a documented tradeoff, since T19 had hand-authored "already deduplicated" Stage 1 output directly rather than exercising that step. Building the missing script and then actually running it against a properly reconstructed multi-framing fixture surfaced two further bugs no amount of reading would have caught:

1. **No deterministic K-pass union/dedup script existed.** Built `scripts/consensus.py`: clusters raw candidates from every framing per artifact type (anchor/content matching for Behaviors and Divergences, structural matching for the rest), writes one `consensus/CONSENSUS-<TYPE>.json` Consensus Run record per type with `agreement_rate`, and assigns stable cross-run IDs for Interfaces and Divergences (REQ-31, using the `IFC_SYNC`/`IFC_ASYNC`/`DVG` counters `state.schema.json` had already reserved for exactly this but nothing had implemented). `rover-discover.md` §3 rewritten to call it explicitly instead of describing the step in prose.
2. **`match_divergences`' fallback matched on the literal placeholder string `"unknown"`** — any two divergences with unresolved `behavior_id`s would spuriously merge regardless of concept, found only because the fixture's raw data legitimately used `"unknown"` as a placeholder (the realistic case, since an agent can't know a Behavior ID that doesn't exist yet). Fixed: the shared-behavior_id fallback now requires both IDs to actually match the `BHV-NNNN` pattern.
3. **`resolve-identity.py` silently discarded fields later stages had added.** When merging a matched candidate, it started from `dict(cand)` (Stage 1's fields only) rather than `dict(match)` (the full existing record) — so re-running Stage 1 after Stage 2 had assigned `context` would wipe every Behavior's Context assignment on the next run. Fixed by starting from the existing record and overlaying only the candidate's non-null fields; regression-tested against all four original T09a scenarios plus a new one (a `context` field surviving three consecutive re-runs) — all pass.

`fixtures/sample-estate/dot-contextrover/` was then rebuilt from scratch through the real pipeline (raw `passes/1/<framing>/*.json` → `consensus.py` → human triage, including rejecting a genuine near-duplicate the ensemble found → `resolve-identity.py` → Stage 2/3 assembly), re-verified against all six T19 criteria, and re-checked for ID stability across two full pipeline runs (not just `resolve-identity.py` in isolation, as T19 originally tested). All still pass. See `fixtures/sample-estate/README.md` for the rebuilt fixture's exact seeded characteristics.

Two further checks — live agent-prompt quality, and functionally exercising Stages 4–8 — followed, and both surfaced their own real findings.

**Live agent dispatch.** Real personations of `behavior-extractor` and `divergence-detector` were run against the fixture source (not just structural checks). Output quality was strong: `behavior-extractor` produced 9 well-evidenced candidates and independently caught a real planted bug (a Kafka publish call that is documented but commented out — a silent no-op). `divergence-detector` found 3 real divergences, including 2 not deliberately seeded, and independently hit the exact `behavior_id` schema tension described next.

**A fourth bug, found by the live dispatch, not by reading:** `divergence.schema.json` required `variants[].behavior_id` to match `^BHV-[0-9]{4}$`, but no discovery-agent candidate can know a Behavior ID that doesn't exist yet (identity is resolved downstream by `resolve-identity.py`). Fixed: `behavior_id` is now optional in the schema; `divergence-detector.md` now says explicitly to omit the field rather than write a placeholder.

**A fifth, larger finding: plugin-owned paths do not resolve the way they were written.** Every agent and command referenced plugin-owned files (`packs/`, `schemas/`, `knowledge/`, `stages.json`, and the gate scripts themselves) as bare relative paths. That only worked because testing happened from inside the plugin's own repository. Confirmed via research (`claude-code-guide`) that Claude Code exposes `${CLAUDE_PLUGIN_ROOT}` to hooks and `${CLAUDE_SKILL_DIR}` to skills, but **no equivalent exists for agent or command markdown bodies** — a real, undocumented platform gap, not a bug in this repo alone. Fixed end-to-end, user-approved design (main-session-resolved absolute paths):

- `schemas/state.schema.json` gains a `plugin_root` field.
- `rover-init.md` gains a Step 0: resolve and verify the plugin's absolute install path once (asking the operator if nothing else exposes it), record it in `state.json`.
- Every other command reads `plugin_root` at its Prerequisites step and resolves every plugin-owned path (`<plugin_root>/scripts/*.py`, `<plugin_root>/stages.json`, `<plugin_root>/packs/...`, `<plugin_root>/knowledge/...`, `<plugin_root>/charter.template.md`, `<plugin_root>/adapters/...`) as an absolute path — never bare.
- Every command that dispatches an agent now explicitly resolves and supplies that agent's needed plugin file(s) as absolute paths in its task context (`pack_path`, `ddd_reference_path`).
- All 9 discovery agents and both `boundary-proposer`/`spec-critic` now say "the path supplied in your task context," never a bare relative path. (`test-adversary` needed no change — it references no plugin-owned file.)
- The gate/utility scripts themselves needed no change: they already resolve their own `schemas/`/`packs/` location via `Path(__file__)`, not cwd — only the *instruction to invoke them* was ever the problem.

`fixtures/sample-estate/dot-contextrover/state.json` now carries a representative `plugin_root`; the full artifact set was re-validated after every fix above (`validate-artifacts.py` full run + `trace-lint.py` Stages 1–4, all clean).

---

## Constitution C1–C10

### C1 — The evidence layer is the product

Build depth follows the mandated order: disciplined extraction (Stage 1) is the deepest part of the build, verification/execution can be shallower.

**Evidence:** 9 discovery agents (`agents/sync-surface-extractor.md` … `agents/redaction-policy-assessor.md`), a dedicated deterministic identity-resolution script (`scripts/resolve-identity.py`, REQ-31a), and the most elaborate stage-specific gate logic in `trace-lint.py` is Stage 1's (Behavior ID+evidence, async consumer evidence, agreement-rate computation, the found-by-one `[record]` review). The full traceability spine (`behavior → context → service → surface → spec clause → characterization test → task → rollout check → retirement entry`) is realized end-to-end across the 26 schemas and `scripts/build-graph.py`'s node/edge model, and proven live in `fixtures/sample-estate/` (T19).

### C2 — Every gate must be machine-checkable

**Evidence:** every `[record]` criterion in `07-stages.md` §3 is implemented in `trace-lint.py` as *"does a schema-valid Approval or Adjudication record exist, bound to the current artifact hash, naming a human decider"* — never as a judgment the script itself renders. `schemas/approval.schema.json` and `schemas/adjudication.schema.json` are the concrete escape hatch. `adjudication.schema.json` additionally enforces, mechanically, that `decided_by` is not one of the 12 known agent names when `kind == "adjudication"` (verified T02).

### C3 — Read-only by default; declare tools explicitly

**Evidence:** all 12 agents declare `tools:` explicitly (no omission/inheritance) — the 9 discovery agents at exactly `Read, Grep, Glob`, `model: sonnet`; the 3 judgment agents at `Read, Grep, Glob`, `model: opus`. Re-verified across the full, final `agents/` directory at T21: zero agents grant `Write`, `Edit`, or `Bash`. `settings/discovery-profile.json` enforces the same allowlist at the permission-profile level with `defaultMode: dontAsk`. Every command that needs to write or run gate scripts runs in the main session (`settings/authoring-profile.json`), never as a subagent.

### C4 — Nothing organization-specific ships

**Evidence:** `charter.template.md` is placeholders only, each commented, with an explicit "never commit the completed file" warning; `.gitignore` excludes `charter.md` from the first commit (T01). Connector specs (`adapters/issue-tracker.md`, `wiki.md`, `vcs.md`) name required MCP tool *capabilities*, never a hardcoded vendor. Final repo-wide `grep -ri` sweep (T21, excluding the read-only `specs/` input pack) for organization markers, internal hostnames, and the banned "zero behavioral change" claim: clean. (The phrase itself appears once, in `README.md`, quoted specifically to explain why it must never be *claimed* — the same legitimate usage `09-glossary.md` §4 itself makes; not a violation.)

### C5 — Minimize execution; prefer reading

**Evidence:** all 10 gate/utility scripts (`validate-artifacts.py`, `trace-lint.py`, `status-report.py`, `build-graph.py`, `graph-query.py`, `render-report.py`, `run-fitness.py`, `resolve-identity.py`, `consensus.py`, plus the `hooks/validate-on-write.py` companion) are Python-stdlib-only — final grep for third-party imports across `scripts/` found none. Every script runs as `python3 scripts/<name>.py` with no setup. The write-gate hook is one committed, reviewed script rather than an inline shell/`jq` one-liner repeated in `hooks.json` (T15) — a direct application of C5's "one committed script, reviewed once" rule.

### C6 — Ensembles only where no oracle exists

**Evidence:** `stages.json` shows `default_k: 3` (ensemble) only at Stage 1 (9 agents × K framings) and Stage 2 (`boundary-proposer` × K, plus the operator's own hypothesis as an equal candidate). Stages 5 and 6 carry exactly one adversarial agent each (`spec-critic`, `test-adversary`) with no `default_k` — single-pass adversarial, not an ensemble. Stages 7 and 8 carry no agents at all. Framing variants (`by-routes`, `by-tests`, `by-call-sites`) vary vantage point per D4, not model tier.

### C7 — Artifacts are data first, documents second

**Evidence:** 26 JSON schemas under `schemas/`, one per structured artifact kind. Every markdown artifact that has a narrative counterpart to a JSON artifact (`design.md` alongside `tactical-model.json`, `adr/*.md` alongside `approval.schema.json` records) has its skill state explicitly that the markdown is generated from / cites the JSON and must add no undocumented facts of its own (`skills/design-doc/SKILL.md`, `skills/adr/SKILL.md`).

### C8 — Language specifics live in packs, nowhere else

**Evidence:** only Stages 1, 6, 7 ever consult a pack (discovery agents' "extraction strategy comes from the language pack" section; `rover-verify.md` reads `packs/<language>/PACK.md` for harness conventions; `scripts/run-fitness.py` delegates to `packs/<language>/fitness.json`). Final grep across `agents/`, `skills/`, `scripts/`, `schemas/`, `adapters/`, `settings/`, `commands/` for language-specific framework/tool tokens (T13) found none outside `packs/` — the sole exception is `run-fitness.py`'s docstring naming the three fitness tools it delegates to (ArchUnit/go-arch-lint/import-linter), which is descriptive text, not logic, and quotes T09's own task description verbatim.

### C9 — No business logic in commands

**Evidence:** all 12 command files reference the relevant skill or schema by path rather than embedding artifact structure; a repo-wide grep for embedded `"required": [...]` / `"properties": {...}` blocks inside `commands/*.md` found none (T16, re-verified T21). Commands select agents, set order, and enforce gates — extraction and artifact-structure logic live in `agents/` and `skills/` respectively.

### C10 — Fail loudly on incomplete evidence

**Evidence:** every evidence-bearing schema supports `"confidence": "unknown"` with a required `reason`; `interface.schema.json`'s `consumers_complete` defaults to `false` and is documented as the single most dangerous false confidence in the method. `scripts/render-report.py` renders unknowns as the literal text `unknown (<reason>)` — verified never blank, never zero (T08). `scripts/resolve-identity.py` never deletes a Behavior absent from a later run; it marks it `unconfirmed` with `last_seen_run` (T09a, REQ-31a).

---

## Seam checklist (`12-extension-seams.md` §6)

All eight verified at T20 with concrete evidence (schema inspection, targeted greps, and reading the conditional logic itself — not just presence checks):

| Seam | Verified by | Result |
|---|---|---|
| S1.1 | `slice.schema.json` requires `oracle_strategy`; `trace-lint.py` rejects `"specification"` with the exact stated message | ✅ |
| S1.2 | Grep of `scripts/`, `agents/`, `commands/` for "legacy system exists"-shaped assumptions | ✅ none found |
| S1.3 | Read `trace-lint.py`'s Stage 6 function — the Redaction check is inside `if rec.get("oracle_strategy") == "characterization":` | ✅ |
| S1.4 | `coverage.schema.json` requires `denominator` | ✅ |
| S1.5 | `rover-transition.md` writes `transition_profile` into `cutover-plan.json`; schema requires it | ✅ |
| S1.6 | `stages.json` is data, keyed by `oracle_strategy`; `rover-discover.md` reads the Stage 1 roster from it, not hardcoded | ✅ |
| S3.1 | All three `packs/*/PACK.md` declare `discovery_method: pattern` | ✅ |
| S3.2 | Grep of all 12 agent prompts for inline grep-pattern-looking content | ✅ none found |

---

## Accepted deviations and judgment calls, with rationale

Ambiguities were resolved by asking wherever the resolution was structural (four `AskUserQuestion` rounds); lower-stakes content/plumbing gaps were resolved with a documented, reversible choice rather than a fifth+ interruption. All are listed here for the record, per this task's own instruction not to improvise silently.

1. **`plugin.json`'s `"//"` comment field** (T01) — `02-plan.md`'s literal template quoted the banned "zero behavioral change" phrase inside its own warning comment, directly breaking T01's grep gate. **User decision:** drop the field entirely.
2. **`gates.jsonl` schema** (T02) — absent from `04-schemas.md`'s "remaining schemas" list despite being a JSON artifact under `.contextrover/`, unlike the analogous graph JSONL files which did get schemas. **User decision:** derive `gate-entry.schema.json` anyway.
3. **Storage location for non-Slice Approval records** (T04) — `roadmap.schema.json` and `cutover-plan.schema.json` have no embedded `approvals[]` field the way `slice.schema.json` does, and no `approvals/` directory exists in the plan's tree. **User decision:** a central `.contextrover/approvals.json`, filtered by an `artifact` field.
4. **`adjudication.schema.json`'s `decided_by` human-identity constraint** (T02) — the given template only carried a natural-language description, not an enforceable rule, yet T02's accept criterion demanded a schema-level constraint. Resolved by adding an `if`/`then` clause rejecting the closed, fully-known v1 agent-name list — a direct formalization of stated intent, not a guess.
5. **Numeric gate thresholds** (T04) — Stage 3's "configured maximum size" and Stage 6's "coverage ≥ threshold" name no value or storage location anywhere in the pack. Resolved by applying the pack's own established pattern (`11-estimation.md` §3 seeds `behaviors_per_pr`, `f_failure`, `f_async` the same way): seeded defaults (`max_slice_work_units = 40`, `coverage_threshold = 0.90`), overridable via `state.json.gate_config`, documented in the script.
6. **Adapter-owner convention for `adapters/*.md`** (T04) — "every legacy Interface has a named adapter owner" must be machine-checkable, but no file-naming or content convention exists for these markdown specs anywhere in the pack. Adopted: one file per Interface (`adapters/<IFC-id>.md`), a line matching `Owner: <name>`.
7. **`dependency-mapper`'s output has no dedicated schema** (T10) — it's raw structural-dependency evidence, distinct from `change-coupling-analyst`'s commit-history-based `coupling.json`; folded into Interface consumer evidence during consensus aggregation rather than becoming its own inventory artifact.
8. **VCS connector's projection scope** (T14) — `01-spec.md` REQ-46's mapping table never names what a version-control connector actually projects. Inferred: Slice status and gate results onto the pull request carrying that Slice's code, stated explicitly in `adapters/vcs.md` as an inference rather than left implicit.
9. **"the concrete tooling table in `02-plan.md`" (T13)** — cited by T13 as the source for language-pack tooling choices; no such table exists anywhere in `02-plan.md`. The only concrete tooling the pack actually names is T09's arch-fitness trio (ArchUnit/go-arch-lint/import-linter); the other five pack sections per language use standard, well-known ecosystem tooling (general software-engineering knowledge, not research).
10. **Path conventions with no explicit file location given** (T03) — `roadmap.json` (Stage 4 output per `07-stages.md`, absent from `02-plan.md`'s tree) placed at `.contextrover/roadmap.json`; the Slice record itself (implied by `slice.schema.json`'s existence but never given a path) placed at `slices/<id>/slice.json`. Both easy, low-risk path choices, not structural decisions.
11. **Five skills with no dedicated 1:1 schema** (T12) — `design-doc`, `adr`, `characterization-suite`, `contract-tests`, `observability-spec` are markdown/code artifacts. Each anchored explicitly to its most semantically adjacent existing schema (e.g. `design-doc` → `tactical-model.schema.json`) rather than fabricating new schemas the pack never called for.

None of these deviations touch a stated requirement's substance — each fills a genuine gap the specs left open, in the direction the surrounding text already pointed.
