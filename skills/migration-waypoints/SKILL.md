---
name: migration-waypoints
description: Defines the content and structure of Migration Waypoints — dated Consumer Migration Workstream checkpoints tying specific teams' readiness to legacy Interface retirement. Reference when assembling or reviewing migration-waypoints.json.
---

# Migration Waypoints

**Extension beyond the base spec pack** — not in `01-spec.md` or `07-stages.md`. Added because per-interface status in the Retirement Register alone doesn't say *which team* must move *by when*, or what a missed migration actually blocks. Defines what a Waypoint record contains. Does not define how a waypoint's status is determined — that comes from the same traffic/consumer evidence `retirement.json` already relies on (`skills/retirement-register/`), never guessed.

## Schema

`schemas/waypoint.schema.json`. One JSON object per waypoint; `migration-waypoints.json` is a JSON array of these.

## Required fields

`id` (`WP-NNNN`), `name`, `target_date`, `teams` (≥1, names from `intake.json.teams[]`), `interfaces` (≥1, `IFC-*` IDs), `status`.

## Content obligations

- **`teams`** must name real teams from the intake roster (`intake.json.teams[].name`) — a waypoint naming a team nobody recorded at intake is not accountable to anyone.
- **`interfaces`** must be legacy Interfaces already tracked in `retirement.json` — a Waypoint doesn't duplicate retirement tracking, it adds a deadline and an owner on top of it.
- **`status` progression is evidence-gated, exactly like `retirement.json`**: `pending → at-risk → met` (every listed interface reached `zero-traffic` or `retired` in `retirement.json` by `target_date`) or `pending → at-risk → missed` (`target_date` passed with an interface still `active`/`deprecated`). Never advance status without checking the interfaces' actual current status first.
- **`rationale`** should say what this milestone actually blocks — usually a Context's Stage 8 decommission step, since Stage 8 sequences by blast radius and a Context can't fully decommission while a Waypoint gating one of its legacy Interfaces is still `pending`/`at-risk`.

## Behavior-ID citation

Waypoints don't cite Behaviors directly — they operate at the Interface and team level, one layer up from the Behavior traceability spine. `evidence` should point at whatever traffic/consumer data justifies the current `status` (the same evidence sources `retirement.json` and `consumer-mapper` use).

## Unknowns

If a team's actual migration progress can't be confirmed by `target_date`, the honest status is `at-risk` or `missed` with the gap stated in `rationale` — never silently leave a stale `pending` past its own target date (Constitution C10).

## Minimal worked example

```json
{
  "id": "WP-0001",
  "name": "Billing team off legacy /invoices by Q3",
  "target_date": "2026-09-30",
  "teams": ["Billing team"],
  "interfaces": ["IFC-SYNC-0002"],
  "status": "pending",
  "rationale": "Gates CTX-0002's Stage 8 decommission step; Billing's own consumers are the last dependency on the legacy invoice endpoint.",
  "evidence": [ { "source": "traffic", "locator": "retirement.json#IFC-SYNC-0002" } ]
}
```
