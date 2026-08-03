---
description: Consumer Migration Workstream driver — cross-cutting, parallel to everything after Stage 5, never gates Stages 6–8. Produces per-consumer migration guides, deprecation notices, and maintains the Retirement Register.
---

# /rover-migrate — Consumer Migration Workstream

Not a numbered stage (`07-stages.md` §4). Cross-cutting, owned by the Engagement directly, not by any Context. Starts once Stage 5 publishes new contracts for a Slice and runs in parallel with everything after. **It never gates Stages 6–8** — do not block on it and do not let it block anything else.

Orchestration only (Constitution C9) — Retirement Register content is defined in `skills/retirement-register/`.

## 1. Prerequisites

At least one Slice must have published contracts (Stage 5 complete for that Slice). Read `plugin_root` from `state.json` — every plugin-owned path below is `<plugin_root>/<relative-path>`, never bare. Load `charter.md` — fail actionably if absent.

## 2. Produce migration guides

For each legacy Interface with known consumers and a newly available replacement contract: draft a per-consumer migration guide showing the call-count reduction evidenced by Stage 1's `inventory/sequences.json` analysis (this is what makes the guide concrete rather than generic — "these N separate calls become this one call"). Draft deprecation notices for the legacy surface.

## 3. Maintain the Retirement Register

Update `retirement.json` entries as consumers actually migrate: `status` progresses `active → deprecated → zero-traffic → retired` as evidence supports each transition, `last_traffic` and `zero_traffic_days` updated from whatever traffic evidence is available. **Do not advance a status without supporting evidence.**

`sunset_authority: null` means the Interface is effectively permanent — surface this prominently rather than letting it sit silently; it is the leading indicator that this workstream will never finish for that Interface (`06-intake.md` §5, E4).

## 4. Maintain Migration Waypoints (extension beyond the base spec pack)

Not in `01-spec.md`/`07-stages.md` — added so this workstream has a dated, team-accountable checkpoint, not just per-interface status. Where a legacy Interface's retirement is meaningful to schedule against (usually because it gates a Context's Stage 8 decommission, or a compliance/contract deadline), write or update a `migration-waypoints.json` entry (`schemas/waypoint.schema.json`, `skills/migration-waypoints/`) naming the team(s) from `intake.json.teams[]` responsible and the Interfaces it covers.

Update each waypoint's `status` from the same evidence `retirement.json` already tracks — `pending` while on track, `at-risk` as `target_date` approaches with an Interface still `active`/`deprecated`, `met` once every listed Interface reaches `zero-traffic`/`retired`, `missed` if `target_date` passes without that. **Never advance status without checking the Interfaces' actual current status first** — same discipline as the Retirement Register itself. Surface `at-risk` and `missed` waypoints prominently; they are the concrete, team-attributable version of the same signal `sunset_authority: null` gives at the Interface level.

## 5. Gate

Run `python3 <plugin_root>/scripts/validate-artifacts.py --dir .contextrover` (no `--stage` — this workstream is cross-cutting, not tied to one numbered stage) against `retirement.json` and `migration-waypoints.json`. There is no `trace-lint.py` gate specific to this workstream and it blocks nothing else; its own completion criterion is the legacy surface being fully decommissioned, tracked in `retirement.json` and reported by `scripts/status-report.py`'s Consumer Migration Stream adoption metric (kept separate from Build Stream conformity, never blended — REQ-13).

Commit `.contextrover/` after any update. No stage tag — this workstream has no single completion gate to tag.
