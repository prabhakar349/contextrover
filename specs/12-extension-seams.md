# Extension Seams — deferred scope and how it plugs in later

v1 is deliberately narrower than earlier drafts. This document records what was cut, why, and **the seams that must exist in v1 so the cut features can be added without rework.**

A seam is cheap to build now and expensive to retrofit. Every seam below is mandatory in v1 even though the feature behind it is not.

---

## 1. Greenfield / Specification oracle — the big one

### Why deferred

A second Oracle Strategy roughly doubles the verification surface: different discovery agents, a different correctness oracle, a different transition stage, a different completion denominator. v1 has no greenfield use case in hand. Building it speculatively means shipping two half-tested paths instead of one working one.

### What v1 must do anyway

**S1.1 — Reserve the discriminator.** Every Slice record carries:

```json
"oracle_strategy": { "enum": ["characterization", "specification"] }
```

v1 validators accept **only** `characterization` and reject `specification` with the message *"Specification oracle is not implemented in this version."* The field is required, not optional — a required field with one legal value is trivial to widen; an absent field means migrating every artifact later.

**S1.2 — Never assume Behaviors came from code.** `behavior.schema.json` already has an `evidence[].source` enum. v1 populates it with `code`, `test`, `traffic`, `stream-metadata`, `commit-history`, `config`. Greenfield will add `interview`, `business-document`, `regulation`. **No code may branch on "evidence exists therefore a legacy system exists."** Treat Behaviors as facts with provenance, not as observations of a running system.

**S1.3 — Do not hard-wire the Stage 6 Redaction Policy gate.** The gate criterion is *"Redaction Policy verdict = GO for every Interface in this Slice"*. It must be expressed as: **if** `oracle_strategy == characterization` **then** require GO. Redaction is meaningless when there is no legacy response to compare against. Writing this as an unconditional check is the single most likely thing to block greenfield later.

**S1.4 — Parameterize the coverage denominator.** Completion is *covered items ÷ total items*. In v1 the item is a Behavior with a passing characterization test. Under a specification oracle it is an acceptance criterion with a passing test. `coverage.json` must name its denominator explicitly rather than hard-coding "behaviors":

```json
{ "denominator": "behaviors", "total": 247, "covered": 231 }
```

**S1.5 — Dispatch Stage 8 on strategy, not on hard-coded cutover.** Brownfield transition is shadow → canary → cutover → decommission. Greenfield is launch. The Stage 8 command must select a transition profile rather than assuming a legacy system exists to shadow against.

**S1.6 — Keep the discovery agent roster in configuration, not in the command.** Stage 1's agent list lives in `stages.json`, keyed by **`default_oracle_strategy`** — an Engagement-level field recorded at intake, *not* the per-Slice `oracle_strategy`, which does not exist until Stage 3. Slices inherit the default and may override it at Solution Outline. v1 ships one key. Adding greenfield adds a second key and a set of elicitation agents — no change to the command.

### What v2 adds

Intake mode question; elicitation agents (business-context, regulation, stakeholder-interview); `acceptance-criteria` as a first-class evidence source; a specification transition profile; per-Slice mode mixing within one Engagement.

**Recorded deviation from the domain model:** the model fixes Mode at Engagement level and immutable. This design places `oracle_strategy` on the **Slice**, permitting mixed engagements. Rationale: a re-decomposition frequently adds genuinely new capability alongside preserved behavior, and forcing two Engagements to model one domain splits the context map. Cost: the "one oracle per engagement" invariant is lost and reporting must aggregate two denominators. Accepted knowingly.

---

## 2. Connectors — observability and chat deferred

**Cut:** observability and chat connectors. **v1 ships:** issue tracker, wiki, version control.

**Seam:** the connector interface (`adapters/ADAPTER-INTERFACE.md`) is already generic — declare required MCP tools, map artifact to external object, key by `contextrover-id`, degrade to `pending` when absent. Adding a connector is a new spec file plus a projection mapping row. **No code change required.** Nothing further needed in v1.

Rationale for the cut: the observability connector is the only one whose value depends on the target system already running, which does not happen until Stage 8. Chat notification is a convenience.

---

## 3. LSP / Serena dual-path discovery

**Cut:** the obligation for every Language Pack to declare both a pattern-based and an LSP-based discovery path.

**Seam S3.1:** the Pack interface declares:

```yaml
discovery_method: pattern        # v1: always "pattern". Reserved: "lsp"
```

**Seam S3.2:** discovery agents receive their extraction strategy from the pack, never inline in the agent prompt. An agent that hard-codes grep patterns in its own system prompt cannot later be handed LSP symbols.

Rationale: LSP raises extraction quality materially but requires an external MCP server, and v1 must work with nothing installed. Adding it later is a pack-level change if S3.2 holds.

---

## 4. Contexture export

**Cut from v1 build tasks; no seam required.** The exporter reads `model/contexts.json` and `model/context-map.json` and writes Contexture's JSON snapshot format. It is a standalone read-only script over already-specified artifacts and can be added at any time without touching anything else.

Keep the intent recorded in `01-spec.md` REQ-45a so the vocabulary alignment argument is not lost.

---

## 5. Evidence graph and HTML report — retained, but scoped

Both **stay in v1** — the report is the leadership-facing artifact and the graph is what makes lint queries tractable. Scope reductions:

- The graph ships with the six named queries in `08` §1.2 and no general query language.
- The report ships the sections in `08` §3.2 and no interactivity beyond sort and filter.
- Neither is a gate. If either fails to generate, the phase still passes and the failure is recorded. **A reporting bug must never block delivery.**

---

## 6. Seam checklist for the implementer

Before declaring the build complete, verify each of these. They are the entire cost of keeping v2 cheap:

| # | Seam | How to verify |
|---|---|---|
| S1.1 | `oracle_strategy` required on every Slice, one legal value | Schema rejects a Slice without it; rejects `specification` with the stated message |
| S1.2 | No code branches on "legacy system exists" | Grep for such assumptions in gate scripts and agent prompts |
| S1.3 | Redaction gate is conditional on `oracle_strategy` | Read the Stage 6 gate implementation |
| S1.4 | `coverage.json` names its denominator | Schema requires the field |
| S1.5 | Stage 8 selects a transition profile | Command reads a profile rather than hard-coding steps |
| S1.6 | Stage 1 agent roster is data, not code | Roster lives in `stages.json` |
| S3.1 | Packs declare `discovery_method` | All three packs have the field |
| S3.2 | Extraction strategy comes from the pack | No grep patterns inline in agent prompts |
