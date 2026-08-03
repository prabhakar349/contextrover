---
name: roadmap
description: Defines the content and structure of the Delivery Roadmap — Stage 4's Increment sequencing, capacity model, and forecast. Reference when assembling or reviewing roadmap.json.
---

# Roadmap

Defines what the Delivery Roadmap contains. Does not define how the forecast is computed — that arithmetic lives in `11-estimation.md` and is implemented once, in `scripts/status-report.py` and the Stage 4 command; this skill only governs the resulting artifact's shape.

## Schema

`schemas/roadmap.schema.json`. A single JSON object — `roadmap.json` is not an array.

## Required fields

`version_hash`, `increments` (≥1), `capacity`, `forecast`.

## Content obligations

- **Increment 0 is always the Walking Skeleton.** `ordinal: 0`, `is_walking_skeleton: true`. Nothing may precede it. Every Increment needs a named `owner` — an Increment without an owner is not yet real.
- **`capacity.binding_constraint`** must be named explicitly (`review` / `integration` / `authoring`) — per `11-estimation.md` §1, review capacity is the constraint that actually matters almost always, and hiding it behind a single date is the one thing this artifact must never do. List every default used because an intake answer was unknown in `capacity.assumptions_used`.
- **`forecast.band`** must reflect the Stage 1 agreement rate honestly (`11-estimation.md` §5: ≥0.90 → ±20%, 0.75–0.90 → ±40%, <0.75 → ±80% with a recommendation to extend Discovery). Never report a narrow band on poorly understood scope.
- **`priority_conflicts`** — where stated business order conflicts with dependency or blast radius, flag it here; never silently override the stated business order, and never silently override dependency ordering either.

## Behavior-ID citation

The roadmap cites Slices, not Behaviors directly — `increments[].slices[]` must include every Slice exactly once (`trace-lint.py --stage 4`); the Behavior-level citation already lives on each Slice.

## Unknowns

Where a capacity input was never answered at intake, use the documented default and list it in `assumptions_used` rather than inventing a number silently.

## Minimal worked example

```json
{
  "version_hash": "sha256:...",
  "increments": [
    { "ordinal": 0, "name": "Walking Skeleton", "slices": ["SLC-0001"], "owner": "Platform team", "is_walking_skeleton": true },
    { "ordinal": 1, "name": "Order placement", "slices": ["SLC-0004"], "owner": "Ordering team" }
  ],
  "capacity": { "binding_constraint": "review", "review_rate": 9, "integration_rate": 12,
                "assumptions_used": ["prs_per_reviewer_per_day defaulted to 3 (F4 unanswered)"] },
  "forecast": { "duration_days": 64, "band": "±40%", "agreement_rate": 0.81, "restale_after": "completion of Increment 0" },
  "priority_conflicts": []
}
```
