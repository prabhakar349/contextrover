# Connector / Adapter Interface

A connector is an external-system integration surface (an MCP server) that ContextRover consumes to project local artifacts outward (09-glossary.md §3). Adapters are thin mapping specs consuming MCP tools, not integrations — the MCP server does the work (decision D8, `02-plan.md` §4). This keeps the plugin dependency-free: nothing in `scripts/` or `agents/` talks to a network, ever (Constitution C5).

Every connector spec in this directory must state all four invariants below explicitly, and must name the MCP tool(s) it requires.

## The four invariants

**1. Local is the single source of truth (REQ-40).** Every artifact under `.contextrover/` is authoritative. An external system never originates data that flows back into `.contextrover/` — if a wiki page or issue is edited externally, that edit has no effect on the local artifact. There is one direction of truth, always.

**2. Projection is one-way (REQ-41).** Local → external, never external → local. Bidirectional sync is explicitly out of scope — it is the dominant failure mode of tools in this category, and this framework does not attempt it. A connector that reads back from its external system to update local state is a defect.

**3. Projection is an idempotent upsert, keyed by `contextrover-id` (REQ-42).** Every projected object carries the source artifact's ID as a label, custom field, or page property named `contextrover-id`. Re-running a projection updates the existing external object found by that key; it never creates a duplicate. `schemas/projection.schema.json` is the local record of this mapping — one record per (artifact, connector) pair, tracking `external_id`, `external_url`, and `status`.

**4. Absence degrades, never fails (REQ-43, REQ-44).** If a connector's required MCP tool is not present in the session, the stage that would have projected still completes normally, and the projection is recorded as `status: "pending"` with a `reason` — never a hard failure. No connector is required for the framework to function; fully air-gapped operation is a tested, supported mode (`01-spec.md` §5.8).

## Capability probe

Every connector is probed for availability before it is configured, and re-probed at the moment of actual use — not assumed available from a stale intake answer (`06-intake.md` §3). `/rover-project <adapter>` always re-probes before acting. This is why invariant 4 says "never fails": availability can change between intake and the moment a projection is attempted, and the framework must handle both the same way.

## Explicit projection only (REQ-47)

No connector fires automatically on stage completion. Writing to an external system is a side effect and must be a deliberate operator action: `/rover-project <adapter>`.

## Connector spec format

Each connector spec in this directory states: which MCP tool(s) it requires (naming the category — issue tracker, wiki, VCS — not a hardcoded vendor, since organization-specific content never ships in this repository, Constitution C4), which artifacts it projects and why (REQ-46), and what "degraded" looks like for that specific connector.

## v1 scope

Ships: `issue-tracker.md`, `wiki.md`, `vcs.md`. Observability and chat connectors are deferred to v2 (`12-extension-seams.md` §2) — the connector interface above is already generic enough that adding one later is a new spec file plus a projection-mapping row, no code change.
