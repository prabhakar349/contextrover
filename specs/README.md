# contextrover — Build Spec Pack

Self-contained specification for building the **contextrover** plugin: a spec-driven framework for re-decomposing N services into M bounded-context-aligned services with no unadjudicated behavioral change.

**These specs are complete. The CLI agent should not need to research anything.** Every decision, format, and tooling choice is stated explicitly. If the agent finds itself wanting to search the web, that is a defect in these specs — record it and ask rather than guessing.

---

## How to run

Place this pack in `specs/` inside an empty git repository, open Claude Code there, and issue:

```
Read every file in specs/ in full, in this order: 00, 09, 07, 01, 12,
02, 04, 06, 08, 11, 03. Ignore 07-phases.md and 10-journey.md — they are
superseded stubs.

Then execute the tasks in specs/03-tasks.md in order. After each task,
verify its acceptance criteria before moving on. Resolve conflicts using
the precedence order below. If anything is ambiguous or underspecified,
stop and ask — do not improvise and do not search the web.
```

Recommended: run with plan mode for the first two tasks, then let it proceed.

---

## Reading order and purpose

| File | Purpose | Audience |
|---|---|---|
| `00-constitution.md` | Non-negotiable principles for **building** this plugin | Builder agent |
| `01-spec.md` | What the plugin must do — requirements, with all research conclusions embedded | Builder agent |
| `02-plan.md` | Repository layout, technical decisions, file-by-file inventory | Builder agent |
| `03-tasks.md` | Ordered, atomic build tasks with acceptance criteria | Builder agent |
| `04-schemas.md` | JSON schemas for every artifact the plugin produces | Builder agent |
| `05-narrative.md` | How to explain the method to each audience | Not part of the build — for you |
| `06-intake.md` | Stage 0 interview, capability probe protocol, derived risks | Builder agent |
| `07-stages.md` | **NORMATIVE** single stage model — nine stages, contracts, gates, state machine | Builder agent + adopting teams |
| `08-knowledge-and-reporting.md` | Evidence graph, artifact git history, HTML report | Builder agent |
| `09-glossary.md` | **NORMATIVE** ubiquitous language. Outranks every other file on terminology | Builder agent — read first |
| `11-estimation.md` | Capacity model, forecast rules, Intake Section F | Builder agent |
| `12-extension-seams.md` | Deferred scope and the **mandatory** seams that keep it cheap to add | Builder agent |
| ~~`07-phases.md`~~, ~~`10-journey.md`~~ | Superseded stubs. Do not implement from them | — |
| `../contextrover-domain-model.md` | The tool's own DDD model — subdomains, contexts, aggregates, invariants | Builder agent + architects |
| `../knowledge/ddd-reference.md` | Canonical DDD as operational rules — aggregate rules, context-map patterns, boundary heuristics, anti-patterns | Agents at runtime (loading map in T17) |
| `../knowledge/modernization-knowledge-store.md` | Agentic modernization prior art by stage | Agents at runtime |

### Precedence

When documents conflict, resolve in this order:

1. `00-constitution.md` — build principles. Non-negotiable, outranks everything.
2. `09-glossary.md` — terminology, always
3. `07-stages.md` — stages, gates, scope
4. `01-spec.md` — requirements
5. `12-extension-seams.md` — seams (mandatory even where the feature is cut)
6. everything else

A conflict not resolved by these rules is a defect. Report it rather than choosing.

**v1 scope is brownfield only.** Greenfield, the observability and chat connectors, LSP dual-path discovery and the Contexture exporter are deferred — but the seams in `12-extension-seams.md` are in scope and are verified by task T20.

---

## The name

**ContextRover.** A rover is an autonomous exploration vehicle: it surveys unfamiliar terrain, maps it, and carries out tasks on the surface. That is the tool — it explores an estate nobody fully understands, maps it into evidence, and executes the delivery from that map.

- Plugin name: `contextrover`
- Command prefix: `rover-` (`/rover-discover`, `/rover-model`, …)
- Working directory: `.contextrover/`
- Projection key on external objects: `contextrover-id`

**Relationship to [Contexture](https://github.com/trustbit/Contexture)** (trustbit, MIT): Contexture is a Bounded Context Canvas wizard for capturing and visualizing a context model — it documents *where you want to be*. ContextRover does the archaeology and delivery to *get there*. Complementary, not competing; the Contexture export adapter (REQ-45a) writes Stage 2 output straight into it. Credit Contexture explicitly in the plugin README.

To rename, replace `contextrover`, `rover-` and `.contextrover/` throughout — do it **before** Task 01 to avoid churn.

---

## What this plugin is not

- Not a code generator for the target services. It generates **evidence, specs, and verification harnesses**; implementation happens through ordinary spec-driven development downstream.
- Not organization-specific. Zero internal content ships in the repo. See `00-constitution.md` §C4.
- Not a replacement for GitHub Spec Kit. It supplies the stage Spec Kit lacks — evidence extraction — and hands off cleanly to conventional SDD after Stage 5.
