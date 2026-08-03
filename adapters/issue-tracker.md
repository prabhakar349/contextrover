---
connector: issue-tracker
---

# Issue Tracker Connector

Satisfies the four invariants in `adapters/ADAPTER-INTERFACE.md`. This is the critical connector (`01-spec.md` REQ-46) — Divergences specifically need a named human owner, and an issue is how that gets one.

## Required MCP tools

An issue-tracker MCP server exposing, at minimum: create issue, update issue (by key), search/find issue by a custom field or label value, and read issue status. Any MCP server matching this shape works (a Jira-compatible, GitHub Issues, or Linear-compatible server, for example) — this spec names the capability, not a vendor, per Constitution C4.

Probed at intake (`06-intake.md` §3) and re-probed at every `/rover-project issue-tracker` invocation. If unavailable, every stage that would project here completes normally and each pending projection is recorded with `status: "pending"` (`schemas/projection.schema.json`).

## What projects here, and why (REQ-46)

| Artifact | Projects to | Why |
|---|---|---|
| Stage tasks (Slices, Increments) | Epics / stories | Delivery tracking where the team already works |
| **Divergence register entries** | One issue per entry needing a decision | **The critical mapping.** Every Divergence needs a named human decision owner; an issue is how it gets one and stays visible until classified |
| Retirement register entries | One tracked issue per legacy Interface, with sunset date | Otherwise the legacy surface silently becomes permanent — the issue is what keeps it on someone's board |

## Idempotent upsert

Key: `contextrover-id`, stored as a custom field or label on the issue (the exact field name is configured at intake, Section D — `06-intake.md` §2). Re-projecting a Divergence or retirement entry updates the existing issue found by that key: title, description, and status sync from the local artifact; it never creates a second issue for the same ID.

## Configuration (collected only if the probe succeeds — `06-intake.md` P2)

Project key, issue type for Slice/Increment tasks, issue type for Divergence decisions, and the field carrying `contextrover-id`.

## Degraded mode

Unavailable → every Divergence, retirement entry, and Slice/Increment still exists and is fully visible in `scripts/status-report.py` and the HTML report; it simply has no external issue yet. Nothing in Stage 0–8 blocks on this connector being present.
