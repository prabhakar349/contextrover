---
description: Explicit projection of local artifacts to an external connector (issue tracker, wiki, or vcs). Never invoked automatically — projection is always a deliberate operator action.
argument-hint: <adapter>
---

# /rover-project `<adapter>` — Explicit Projection

Orchestration only (Constitution C9) — connector behavior is defined in `adapters/ADAPTER-INTERFACE.md` and the named connector's own spec (`adapters/issue-tracker.md`, `adapters/wiki.md`, `adapters/vcs.md`). **This command is never invoked automatically by any stage command** (REQ-47) — writing to an external system is a side effect and must be deliberate.

## 1. Re-probe

Read `plugin_root` from `.contextrover/state.json` first — `<adapter>`'s own spec (`<plugin_root>/adapters/<adapter>.md`) is a plugin-owned file and cannot be resolved as a bare relative path from the target repository's working directory.

Availability at intake time does not guarantee availability now (`06-intake.md` §3). Before doing anything else, re-probe whether `<adapter>`'s required MCP tool(s) are present in the current session, exactly as Section D of intake did. Never trust `intake.json.adapters.<adapter>.status` as still current — probe again.

- **Unavailable** → stop, report why (naming the missing MCP tool and how to connect it), and confirm this is not a failure: every artifact this connector would have projected remains fully available locally and can be projected later. Do not write `pending` projection records speculatively if the connector was never even reachable enough to attempt one — only mark `pending` for artifacts you attempted and the connector itself reported as not-yet-processed.
- **Available** → continue.

## 2. Project

Using the REQ-46 mapping table in `<adapter>`'s own spec, find every local artifact of the kinds that connector handles which has not yet been projected, or whose local content has changed since its last projection (compare current content hash to the last recorded `projection.schema.json` record's implied state). For each: **idempotent upsert keyed by `contextrover-id`** — find the existing external object by that key and update it, or create it if none exists. Never create a duplicate for an ID that already has an external object.

Write or update a `schemas/projection.schema.json` record for each artifact projected, with `status: "projected"` on success or `status: "failed"` with a `reason` on failure — a failed individual projection does not abort the others; continue through the remaining artifacts and report the full set of failures at the end.

## 3. No gate

Projection is not a stage gate and does not append to `gates.jsonl` in the sense a stage gate does — it is a side effect, not a traceability checkpoint. Commit `.contextrover/projections/<adapter>.json` after the run so the projection state itself is versioned locally, consistent with local-is-source-of-truth (invariant 1).
