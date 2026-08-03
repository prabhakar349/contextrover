---
name: slice-outline
description: Defines the content and structure of a Slice record and its Size — the Stage 3 Solution Outline unit of delivery. Reference when assembling or reviewing slices/<id>/slice.json and size.json.
---

# Slice Outline

Defines what a Slice record and its Size contain. Does not define how Behaviors get partitioned into Slices — that judgment happens during Stage 3 drafting; this skill only governs the resulting artifact shapes.

## Schemas

`schemas/slice.schema.json` (`slices/<id>/slice.json`) and `schemas/size.schema.json` (`slices/<id>/size.json`).

## Required fields — Slice

`id` (`SLC-NNNN`), `workstream` (`WS-NNNN`), `oracle_strategy`, `behaviors`, `state`. `oracle_strategy` is required on every Slice, always — v1 accepts only `"characterization"`; `"specification"` is a reserved value for a future oracle and must be rejected in v1 with the message *"Specification oracle is not implemented in this version."* (seam S1.1).

## Required fields — Size

`slice`, `behaviors`, `interfaces_sync`, `interfaces_async`. **Contains no dates** — `size.json` is scope only; dates belong exclusively to Stage 4's roadmap. A `duration_days` field on a `size.json` is a schema violation, not a convenience.

## Content obligations

Every Behavior in scope must be assigned to **exactly one** Slice — `behaviors[]` is how the Stage 3 gate (`trace-lint.py --stage 3`) checks that no Behavior is left unassigned or double-assigned. Track `failure_path_behaviors`, `divergences_open`, `consumers_affected`, and `data_migration_required` in Size — these are the real cost drivers Stage 4's capacity model reads (`11-estimation.md` §2.1), not vanity metrics.

## Behavior-ID citation

`behaviors[]` on the Slice record is itself the citation — every Behavior ID it lists is now this Slice's responsibility to deliver and verify.

## Unknowns

If a Slice's true size is not yet knowable (e.g. failure-path coverage undetermined), say so in the accompanying PRD rather than guessing a `size.json` number — an inflated or deflated size number corrupts every roadmap forecast downstream.

## Minimal worked example

```json
{ "id": "SLC-0004", "name": "Order placement", "workstream": "WS-0001", "context": "CTX-0001",
  "oracle_strategy": "characterization", "behaviors": ["BHV-0011", "BHV-0012", "BHV-0042"],
  "state": "Outlined" }
```

```json
{ "slice": "SLC-0004", "behaviors": 3, "failure_path_behaviors": 1,
  "interfaces_sync": 1, "interfaces_async": 1, "divergences_open": 0,
  "consumers_affected": 2, "data_migration_required": false }
```
