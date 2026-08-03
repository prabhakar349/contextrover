---
name: tactical-model
description: Defines the content and structure of a Slice's Tactical Model — aggregates, invariants, domain events, commands, and policies. Reference when assembling or reviewing slices/<id>/tactical-model.json.
---

# Tactical Model

Defines what a Tactical Model contains. Does not decide the boundaries — those were fixed at Stage 2; this is the per-Slice detailed design within an already-approved Context, just-in-time (`07-stages.md` Stage 5).

## Schema

`schemas/tactical-model.schema.json`. A single JSON object per Slice — `slices/<id>/tactical-model.json` is not an array.

## Required fields

`slice`, `aggregates` (≥1, each with `name`, `root`, `invariants`).

## Content obligations — Vernon's rules, applied (`knowledge/ddd-reference.md` §2.1)

- **Every aggregate declares at least one invariant.** An aggregate with no invariant is a data bag, not a domain model — the Stage 5 gate rejects this (`trace-lint.py --stage 5`). The test: can you state the rule that must hold at the end of every transaction? If not, it isn't an aggregate.
- **Reference other aggregates by identity only** — never embed one aggregate inside another's structure.
- **No invariant should require a synchronous call to a sibling aggregate.** This is the specific judgment criterion the Stage 5 architecture-review approval must cover explicitly.
- **Domain events are named in the past tense** (`OrderPlaced`, not `OrderTableUpdated`); **commands are named in the imperative** (`PlaceOrder`). A domain expert should recognize the event name.

## Behavior-ID citation

Every invariant's `behaviors[]` must be non-empty — this is both "every aggregate declares ≥1 invariant" and "every design clause cites a Behavior ID" from the Stage 5 gate, in one field. A Behavior assigned to this Slice (per its `slice.json.behaviors[]`) that is cited by no invariant here is an orphan Behavior in the Slice — also a gate failure.

## Unknowns

If an invariant is suspected but its exact statement isn't settled, do not add a placeholder invariant just to satisfy the "≥1 invariant" check — an invariant that doesn't actually hold is worse than an aggregate flagged as needing more design work.

## Minimal worked example

```json
{
  "slice": "SLC-0004",
  "aggregates": [
    {
      "name": "Order", "root": "Order",
      "entities": ["OrderLine"], "value_objects": ["Quantity", "Money"],
      "invariants": [
        { "statement": "An Order must contain at least one OrderLine with quantity > 0", "behaviors": ["BHV-0042"] }
      ]
    }
  ],
  "domain_events": [ { "name": "OrderPlaced", "aggregate": "Order" } ],
  "commands": [ { "name": "PlaceOrder", "aggregate": "Order" } ],
  "policies": [ "When OrderPlaced, notify billing-svc" ]
}
```
