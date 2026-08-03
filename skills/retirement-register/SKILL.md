---
name: retirement-register
description: Defines the content and structure of the Retirement Register — every legacy Interface, its known consumers, and its sunset status. Reference when assembling or reviewing retirement.json.
---

# Retirement Register

Defines what a Retirement Register entry contains. Every legacy Interface gets one entry from Stage 1 onward (v0, per REQ-08) — this is not a Stage 8 artifact created late; it starts as soon as the Interface Inventory does, and is maintained by the Consumer Migration Workstream throughout.

## Schema

`schemas/retirement.schema.json`. One JSON object per legacy Interface; `retirement.json` is a JSON array of these.

## Required fields

`interface_id`, `status` (`active` / `deprecated` / `zero-traffic` / `retired`).

## Content obligations

- **`sunset_authority: null` means the interface is effectively permanent.** This is not a placeholder to fill in "later" — it is a real, reportable state, and `scripts/status-report.py` and the HTML report both surface this count prominently, because it is the leading indicator that the Consumer Migration Stream will never finish.
- **`known_consumers`** starts from whatever `consumer-mapper` and `dependency-mapper` evidence supports at Stage 1 — an incomplete list here is expected early and should improve as evidence accumulates, not be treated as final.
- **`zero_traffic_days`** and **`last_traffic`** are what justify a status transition to `zero-traffic` and eventually `retired` — a status change with no supporting traffic data behind it is not yet earned.
- **`migration_guide`** should link to the per-consumer guide once the Consumer Migration Workstream produces one (showing the call-count reduction evidenced by Stage 1's sequence analysis).

## Behavior-ID citation

The register does not cite Behaviors directly — it tracks Interfaces. The traceability back to Behaviors runs through the Interface Inventory (`behavior.interfaces[]`); an Interface cannot be safely retired while Behaviors still cite it as their only implementation.

## What this skill does not cover

Deciding *when* to retire — that is the sunset authority named at intake (`06-intake.md` E4), a governance decision this register records the consequences of, not one it makes.

## Minimal worked example

```json
{
  "interface_id": "IFC-SYNC-0002",
  "known_consumers": ["legacy-mobile-client"],
  "status": "deprecated",
  "sunset_date": "2027-01-15",
  "sunset_authority": "VP Engineering",
  "last_traffic": "2026-07-30T00:00:00Z",
  "zero_traffic_days": 0,
  "migration_guide": "projections/wiki/migrate-legacy-mobile-client.md"
}
```
