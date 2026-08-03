---
name: design-doc
description: Defines the content and structure of a Slice's detailed design document. Reference when assembling or reviewing slices/<id>/design.md.
---

# Design Doc

Defines what `design.md` must contain, as the human-readable narrative companion to `tactical-model.json` (Constitution C7 — the JSON is the data of record; this markdown explains it, it does not add undocumented facts of its own).

## Schema anchor

There is no dedicated JSON schema for `design.md` itself — it is generated narrative, not an independently authored data artifact. Its citation obligations mirror `schemas/tactical-model.schema.json`: every clause in this document must be traceable to the same `invariants[].behaviors[]` data that grounds the Tactical Model, because the Stage 5 gate (`trace-lint.py --stage 5`) requires "every design clause cites a Behavior ID."

## Required sections

1. **Scope** — which Slice, which Context, which Behaviors are in scope (list the Behavior IDs).
2. **Aggregates** — one subsection per aggregate: its invariants (restated in prose, each with its Behavior ID citation inline), entities, value objects.
3. **Domain events and commands** — named exactly as in `tactical-model.json`, with the trigger/effect described in prose.
4. **Legacy adapter approach** — for every legacy Interface in scope, name the adapter pattern used (Anticorruption Layer by default — `knowledge/ddd-reference.md` §5) and who owns it.
5. **Open questions** — anything `spec-critic` should specifically attack, or that is still genuinely undecided. Do not hide uncertainty to look more finished than the design actually is.

## Behavior-ID citation

Every clause describing a rule, a validation, or a side effect needs an inline citation like `(BHV-0042)`. An uncited clause is either an unevidenced addition the critic should flag, or a citation that was simply forgotten — either way, `spec-critic` (`agents/spec-critic.md`) is specifically instructed to hunt for these.

## What this skill does not cover

How the design was arrived at, or what evidence was gathered to inform it — that is Stage 1/2 discovery's job, already done by the time this document is written (Constitution C9).

## Minimal worked example (excerpt)

```markdown
## Aggregates

### Order (root: Order)
- Invariant: An Order must contain at least one OrderLine with quantity > 0 (BHV-0042)
- Entities: OrderLine
- Value objects: Quantity, Money
```
