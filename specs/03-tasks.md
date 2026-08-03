# Build Tasks — ContextRover v1

Execute in order. Verify each task's acceptance criteria before proceeding. Do not batch. Do not skip ahead.

If a task is ambiguous, **stop and ask.** Do not improvise and do not search the web. Ambiguity here is a defect in the specs.

**Scope:** v1 is brownfield only. Deferred features and the seams they require are in `12-extension-seams.md` — the seams are **in scope** even though the features are not.

**Authorities:** `09-glossary.md` for terminology, `07-stages.md` for stages and gates, `01-spec.md` for requirements, `00-constitution.md` for build principles.

---

## T01 — Repository scaffold

Create `.claude-plugin/plugin.json`, `README.md`, `LICENSE` (MIT), `.gitignore`, and the full directory tree from `02-plan.md` §2 **including** `scripts/`, `packs/`, `adapters/`, `schemas/`, `settings/`, `knowledge/`, `fixtures/`.

`plugin.json` description must read: *"Domain-Driven Modernization: re-decompose N services into M bounded-context-aligned services with no unadjudicated behavioral change."* The phrase "zero behavioral change" must not appear anywhere in the repository (`09-glossary.md` §4).

`.gitignore` (plugin repo): `charter.md`, `.contextrover/`, `__pycache__/`.

**Accept:** `plugin.json` parses and contains the required description verbatim. `grep -ri "zero behavioral change"` returns nothing. Tree matches §2 including the directories named above.

---

## T02 — Schemas

Create every schema in `04-schemas.md` — both the evidence schemas (§§1–6) and the delivery schemas (§7). JSON Schema draft 2020-12, stdlib-validatable.

Every artifact written under `.contextrover/` must have a schema. If you find an artifact with none, stop and ask.

**Accept:** every schema parses, declares `$schema`/`$id`/`title`/`type`/`required`. `slice.schema.json` requires `oracle_strategy` with enum `["characterization","specification"]`. `coverage.json` requires `denominator`. `adjudication.schema.json` constrains `decided_by` to a human identity when `kind == "adjudication"`.

---

## T03 — `scripts/validate-artifacts.py`

Validates `.contextrover/` artifacts against `schemas/`. Stdlib only — implement required-field, type, enum and pattern checking directly; do not import `jsonschema`.

`python3 scripts/validate-artifacts.py [--stage N] [--dir .contextrover]`. Exit 0 valid, 1 invalid, errors to stderr as `<file>:<pointer>: <message>`.

**Accept:** exits 1 with a precise message on an invalid fixture; 0 on a valid one.

---

## T04 — `scripts/trace-lint.py`

The traceability gate. **Every criterion marked with a script in `07-stages.md` §3 must be implemented here or in the script named there.** Implement per stage:

| Stage | Checks |
|---|---|
| 1 | every Behavior has ID + ≥1 evidence; every async Interface has consumer evidence or explicit `consumers_complete:false`; agreement rate computed |
| 2 | every Behavior maps to exactly one Context; zero `unclassified` Divergences; every Context owns ≥1 aggregate root |
| 3 | every Behavior assigned to exactly one Slice; every Slice has acceptance criteria + `size.json`; no Slice over max size; `oracle_strategy == "characterization"` |
| 4 | every Slice appears once in the roadmap; Increment 0 is the Walking Skeleton; every Increment has an owner; capacity model present with binding constraint named |
| 5 | every aggregate declares ≥1 invariant; every design clause cites a Behavior ID; no orphan Behaviors in the Slice; every legacy Interface has a named adapter owner |
| 6 | **if** `oracle_strategy == "characterization"`, Redaction Policy = GO for every Interface in the Slice (seam S1.3); coverage ≥ threshold; failure-path coverage reported separately |

Also, at every stage: **[record]** criteria — verify a schema-valid approval record exists naming a human decider and bound to the artifact version hash.

Boundary span (a Behavior touching >1 target service) is a **warning**, not an error — sagas are legitimate.

`python3 scripts/trace-lint.py [--stage N] [--format text|json]`. Exit 0 clean, 1 errors.

**Accept:** seeded orphan → exit 1 naming the ID. Clean fixture → 0. Boundary span → 0 with warning. A Slice missing its approval record at a `[record]` gate → exit 1.

---

## T05 — `scripts/status-report.py`

Rolls up Engagement / Context / Slice / Workstream state from `state.json` and artifacts. **No network** (REQ-32).

Reports: per-stage status; Build Stream conformity %; Consumer Migration Stream adoption % — **separate, never blended**; ensemble agreement distribution; Divergences by classification; unresolved high risks; count of Interfaces with `sunset_authority: null`.

**Accept:** produces a report from a fixture. No `urllib`/`socket`/`http`/`requests` imports.

---

## T06 — `scripts/build-graph.py`

Regenerates `.contextrover/graph/{nodes,edges}.jsonl` from artifacts. Derived, never authored; full rebuild each run; every edge carries provenance.

**Accept:** valid graph from a fixture; two consecutive runs produce byte-identical output.

---

## T07 — `scripts/graph-query.py`

The six queries in `08-knowledge-and-reporting.md` §1.2. `--format text|json`. No general query language.

**Accept:** each query correct against a fixture seeded with an orphan and a boundary span.

---

## T08 — `scripts/render-report.py`

Single self-contained HTML file to `.contextrover/report/index.html`. All CSS/JS/data inlined; no CDN; opens offline. Stdlib only; charts as hand-emitted inline SVG. Sections per `08` §3.2.

**Not a gate.** If rendering fails the stage still passes and the failure is recorded (`12-extension-seams.md` §5).

**Accept:** output contains no `http://`, `https://` or `//cdn` except user-supplied repository links. Unknowns render as "unknown" with reason, never as zero or blank. Build Stream and Consumer Migration gauges are separate.

---

## T09 — `scripts/run-fitness.py`

Executes the architecture fitness functions declared by a Slice's language pack and reports pass/fail per rule. Delegates to the pack's tooling (ArchUnit, go-arch-lint, import-linter) via a documented invocation contract; does not reimplement them.

**Accept:** returns per-rule results against a fixture; exits non-zero if any rule fails.

---

## T09a — `scripts/resolve-identity.py`

Implements REQ-31a exactly: anchor match, then content match at Jaccard ≥ 0.80, then new ID from `state.json.counters`. Deterministic, stdlib, no model calls. Marks unmatched prior Behaviors `unconfirmed`; never deletes.

**Accept:** two consecutive runs over an unchanged fixture produce byte-identical IDs; a renamed summary within similarity threshold keeps its ID; a genuinely new behavior gets the next counter value; a removed behavior becomes `unconfirmed` rather than disappearing.

---

## T10 — Discovery agents (read-only)

In `agents/`: `sync-surface-extractor`, `async-surface-extractor`, `behavior-extractor`, `dependency-mapper`, `consumer-mapper`, `call-sequence-analyst`, `change-coupling-analyst`, `divergence-detector`, `redaction-policy-assessor`.

All declare exactly `tools: Read, Grep, Glob` and `model: sonnet`.

Each prompt states: its single output artifact and schema; that its **extraction strategy comes from the language pack, never inline** (seam S3.2); that undeterminable findings are recorded as explicit `unknown` with a reason; that it writes only under `.contextrover/passes/`; and that recall is favoured over precision.

`async-surface-extractor` additionally captures schema, partition key, ordering guarantee, delivery semantics, retry/DLQ behaviour and consumer evidence. `change-coupling-analyst` mines commit history for co-change frequency.

**Accept:** valid frontmatter throughout; **no agent in `agents/` declares `Write`, `Edit`, `Bash` or any MCP tool**; no grep patterns appear inline in any agent prompt.

---

## T11 — Judgment agents

`boundary-proposer` (`model: opus`), `spec-critic` (`model: opus`), `test-adversary` (`model: opus`). All declare `tools: Read, Grep, Glob` — they analyse and return findings; the invoking command writes.

- `boundary-proposer` — proposes contexts from Behaviors, coupling and the event catalogue. Prompt must state explicitly that it **proposes and never decides**, and must surface practical coupling and operational cost alongside theoretical cleanliness.
- `spec-critic` — attacks a draft for ambiguity, missing error cases, unstated assumptions, uncited clauses.
- `test-adversary` — finds behaviors that would pass a characterization suite while differing from the original. Must probe failure paths, timeouts, partial completion and event ordering specifically.

The **consensus-runner is not a subagent.** Aggregation and adjudication-record writing happen in the main session, because a subagent cannot surface an approval prompt and an Adjudication requires a human decider.

**Accept:** all three present with the stated tools and model; `boundary-proposer` contains the propose-not-decide constraint; no `consensus-runner` file exists under `agents/`.

---

## T12 — Skills

One per artifact kind: interface-inventory, behavior-inventory, divergence-register, adjudication-record, context-model, variation-policy, slice-outline, acceptance-criteria, roadmap, tactical-model, design-doc, adr, characterization-suite, contract-tests, observability-spec, cutover-plan, retirement-register.

Each defines the artifact's **content and structure only** — never how evidence is gathered (C9). Each states its schema path, required fields, Behavior-ID citation obligations, and a minimal worked example.

**Accept:** every SKILL.md has `name` and `description` frontmatter and references a schema in `schemas/`.

---

## T13 — Language packs

`packs/PACK-INTERFACE.md` plus `java/`, `go/`, `python/`. Sections per `01-spec.md` REQ-52, using the concrete tooling table in `02-plan.md`.

Every pack declares `discovery_method: pattern` (seam S3.1). Every pack owns its extraction patterns — agents read them from here.

**Accept:** all three implement every interface section and declare `discovery_method`; no language-specific content exists outside `packs/`.

---

## T14 — Connectors

`adapters/ADAPTER-INTERFACE.md` plus `issue-tracker.md`, `wiki.md`, `vcs.md`. **Observability and chat are deferred** (`12-extension-seams.md` §2).

The interface doc states the four invariants: local is source of truth; one-way projection; idempotent upsert keyed by `contextrover-id`; degrade to `pending` when MCP tools are absent.

**Accept:** three connector specs, each naming its required MCP tools; none a hard dependency; all four invariants stated.

---

## T15 — Permission profiles, hooks, stage configuration

- `settings/discovery-profile.json` — allow only `Read`, `Grep`, `Glob`; `permissionMode: dontAsk`
- `settings/authoring-profile.json` — ask-gated, main session
- `hooks/hooks.json` — on write to `.contextrover/**`, run `validate-artifacts.py`; block on failure
- `stages.json` — the agent roster per stage, **keyed by `oracle_strategy`** with one key `characterization` (seam S1.6)

**Accept:** profiles parse; discovery profile grants no write or execute tool; `stages.json` is keyed by oracle strategy.

---

## T16 — Commands

`commands/rover-{init,discover,model,outline,roadmap,design,verify,execute,transition,migrate,status,project}.md`.

`rover-migrate` drives the Consumer Migration Workstream (`07-stages.md` §4): per-consumer migration guides, deprecation notices, Retirement Register maintenance. It is cross-cutting and **never gates Stages 6–8**.

Each stage command: check `state.json` for prerequisites → load `charter.md` (fail actionably if absent) → dispatch the agents named in `stages.json` → run the gate scripts named in `07-stages.md` §3 → append to `gates.jsonl` → commit `.contextrover/` → update `state.json`.

- `rover-init` runs the full six-section intake (`06-intake.md`), Access Probes **before** asking system-specific config, derived risk computation, and `git init` in `.contextrover/`. Copies `charter.template.md` to `charter.md` if absent **and stops with instructions**.
- `rover-verify` writes `harness.lock` at the gate (`07-stages.md` §2).
- `rover-execute` verifies `harness.lock` is unchanged before any other gate check; on mismatch it fails and demands re-approval.
- `rover-project <connector>` re-probes availability before acting; never invoked automatically.

Commands orchestrate only — no extraction logic, no artifact structure (C9).

**Accept:** every command matches its contract in `07-stages.md` §3; `rover-init` fails actionably on a missing charter and probes before configuring; `rover-execute` checks the harness lock first; no command file contains artifact field definitions.

---

## T17 — Charter template and knowledge corpus

`charter.template.md` — placeholders only, each commented, with an explicit warning never to commit the completed file. Sections: architecture standards; security and compliance baselines; observability requirements; naming conventions; approval matrix; the agreed success metric ("zero boundaries that do not correspond to a bounded context"); sunset authority.

Copy both supplied corpus files into `knowledge/`:

- `ddd-reference.md` — canonical DDD written as operational rules: subdomain classification, context-map patterns, Vernon's four aggregate rules, boundary heuristics in priority order, brownfield patterns, anti-patterns, canonical sources
- `modernization-knowledge-store.md` — agentic modernization prior art, organized by the stage it informs

**Agents reference these by path in their system prompts, never inline.** Loading map:

| Agent / skill | Loads |
|---|---|
| `boundary-proposer` | `ddd-reference.md` §§1, 4, 6 |
| Tactical Design skills (`tactical-model`, `context-model`) | `ddd-reference.md` §2 |
| `/rover-model` command | `ddd-reference.md` §§1, 3 |
| `spec-critic` | `ddd-reference.md` §6 (anti-patterns) |
| `divergence-detector` | `ddd-reference.md` §1.2 (linguistic boundary test) |
| Discovery agents | `modernization-knowledge-store.md` §1 |

The anti-nanoservice check and the boundary heuristic ordering used by `trace-lint.py` derive from `ddd-reference.md` §§2.1 and 4. If they drift apart, the reference wins and the lint is the defect.

**Accept:** template contains no real values; both corpus files present in `knowledge/`; every agent in the loading map references its section by path; no DDD rule is restated inline in an agent prompt.

---

## T18 — README

For an outside adopter with no context: what the method is, the one-line positioning, the nine stages and their gates, quickstart, the framework/charter separation and why it matters, extension points, credit to Contexture and the knowledge-corpus sources, and an explicit statement that the tool produces evidence, specs and harnesses — **not** target implementations.

Document the nested `.git` in `.contextrover/` — it surprises people.

**Accept:** an outside reader can install and run Stage 1 from the README alone.

---

## T19 — Fixtures and end-to-end verification

Build `fixtures/sample-estate/`: three trivial services in different languages, overlapping behavior with a deliberate Divergence, one published event stream, and a seeded orphan.

Run Stages 0–3 and confirm:

1. Artifacts schema-valid
2. IDs stable across two consecutive Stage 1 runs, via `resolve-identity.py` (REQ-31a)
3. The seeded Divergence appears and blocks the Stage 2 gate while `unclassified`
4. `trace-lint.py` behaves correctly on the seeded orphan
5. Everything completes with **no connector configured**
6. `grep -ri` finds no organization-specific content

Human-in-the-loop steps (Stage 0 interview, Stage 2 adjudication) are exercised with recorded fixture responses, not run unattended.

**Accept:** all six confirmed.

---

## T20 — Seam verification

Verify every row of the seam checklist in `12-extension-seams.md` §6. These are the entire cost of making v2 cheap; a missing seam is a build failure, not a nice-to-have.

**Accept:** all eight seams verified, evidence recorded.

---

## T21 — Final review

Re-read `00-constitution.md` and verify C1–C10 hold across the built repository. Produce `BUILD-REPORT.md` listing each principle with evidence, plus any accepted deviations with rationale.

**Accept:** `BUILD-REPORT.md` addresses all ten principles and the eight seams.
