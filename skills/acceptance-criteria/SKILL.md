---
name: acceptance-criteria
description: Defines the content and structure of a Slice's Acceptance Criteria. Reference when assembling or reviewing slices/<id>/acceptance-criteria.json.
---

# Acceptance Criteria

Defines what an Acceptance Criterion record contains. In v1 (characterization oracle), acceptance criteria restate what the characterization suite must prove; under a future specification oracle (seam S1.1) they would instead carry the scope directly.

## Schema

`schemas/acceptance-criteria.schema.json`. One JSON object per criterion; `slices/<id>/acceptance-criteria.json` is a JSON array of these.

## Required fields

`id` (`AC-NNNN`), `slice` (`SLC-NNNN`), `statement` (≥10 characters — a real assertion, not a restated Behavior summary), `behaviors`.

## Content obligations

Every Slice needs at least one Acceptance Criterion, and every criterion should cite the Behavior(s) it proves — in v1 `behaviors[]` should be non-empty for every criterion, since there is no other oracle yet to carry the scope. Set `failure_path: true` for criteria specifically about failure, timeout, or partial-completion behavior, and make sure such criteria actually exist — a Slice whose acceptance criteria are all happy-path is under-specified before a single test is written.

## Behavior-ID citation

`behaviors[]` is the citation. A criterion with an empty `behaviors[]` under `oracle_strategy: "characterization"` has nothing anchoring it to observed system behavior — it is closer to a wish than a criterion.

## Unknowns

If a criterion's exact boundary is still under discussion, write it as precisely as currently possible and flag the open question in the accompanying PRD — do not leave the `statement` vague to avoid committing.

## Minimal worked example

```json
{
  "id": "AC-0009",
  "slice": "SLC-0004",
  "statement": "An order placement request with quantity <= 0 is rejected with the same error code and message the legacy system returns",
  "behaviors": ["BHV-0042"],
  "failure_path": true
}
```
