---
connector: wiki
---

# Wiki / Docs Connector

Satisfies the four invariants in `adapters/ADAPTER-INTERFACE.md`.

## Required MCP tools

A wiki/docs MCP server exposing, at minimum: create page, update page (by a stable key — title, path, or page ID), and read page metadata. Any MCP server matching this shape works (a Confluence-compatible, Notion-compatible, or plain-git-docs server, for example) — this spec names the capability, not a vendor, per Constitution C4.

Probed at intake (`06-intake.md` §3) and re-probed at every `/rover-project wiki` invocation. If unavailable, every stage that would project here completes normally and each pending projection is recorded with `status: "pending"`.

## What projects here, and why (REQ-46)

| Artifact | Projects to | Why |
|---|---|---|
| PRD (`slices/<id>/prd.md`) | Wiki page | Review and durable reference for product and tech leads |
| ADRs (`adr/*.md`) | Wiki pages | Durable architecture rationale, findable outside the git history of `.contextrover/` |
| Design doc (`slices/<id>/design.md`) | Wiki page | Review surface for architecture review approval |

## Idempotent upsert

Key: `contextrover-id`, stored as a page property or a recognizable marker in the page (e.g. a fixed-format comment or custom field, depending on what the target wiki system supports). Re-projecting a PRD, ADR, or design doc updates the existing page found by that key rather than creating a duplicate page each time the source markdown changes.

## Configuration (collected only if the probe succeeds)

Target space/workspace, parent page under which projected pages are created, and the property or convention carrying `contextrover-id`.

## Degraded mode

Unavailable → PRDs, ADRs, and design docs remain fully readable as markdown under `.contextrover/`; they are simply not mirrored to the wiki. Stage 3 and Stage 5 gates do not depend on this connector.
