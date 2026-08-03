---
connector: vcs
---

# Version Control Connector

Satisfies the four invariants in `adapters/ADAPTER-INTERFACE.md`.

## Required MCP tools

A version-control MCP server exposing, at minimum: read/create/update pull request, and read/set a label or status check on a pull request or commit. Any MCP server matching this shape works (a GitHub-compatible or GitLab-compatible server, for example) — this spec names the capability, not a vendor, per Constitution C4.

Probed at intake (`06-intake.md` §3) and re-probed at every `/rover-project vcs` invocation. If unavailable, every stage that would project here completes normally and each pending projection is recorded with `status: "pending"`.

## What projects here, and why

`01-spec.md` REQ-46's projection table does not name a VCS row explicitly; this connector's scope is inferred from the same table's spirit and stated here plainly rather than left implicit:

| Artifact | Projects to | Why |
|---|---|---|
| Slice status + PRD summary (Stage 7 execution) | The pull request carrying that Slice's target-service changes | Ties a Slice's delivery back to its ContextRover identity at the point of code review, where a reviewer is actually looking |
| Gate results for a Slice (`gates.jsonl`, filtered) | A status check or comment on the pull request | Makes the objective gate outcome visible exactly where the reviewer approves the merge, without requiring them to open the HTML report |

This is a narrower, more targeted surface than the issue tracker's epics/stories — it is about the specific PR a Slice's code lands in, not general delivery tracking.

## Idempotent upsert

Key: `contextrover-id`, stored as a PR label (e.g. `contextrover-id:SLC-0004`) or a fixed-format marker in the PR description. Re-projecting updates the same PR's description/status check rather than opening a new PR or duplicating a comment thread.

## Degraded mode

Unavailable → Stage 7 execution proceeds exactly as it would otherwise (this connector never authors the target implementation — that is ordinary SDD downstream, `01-spec.md` §4); the Slice's gate outcomes are simply not mirrored onto a pull request, and remain fully visible in `.contextrover/gates.jsonl` and the HTML report.
