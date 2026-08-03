---
name: adjudication-record
description: Defines the content and structure of Consensus Run and Adjudication records — the mechanical ensemble output and the accountable human decision over it. Reference when writing to consensus/*.json or adjudications/*.json.
---

# Adjudication Record

Defines what a Consensus Run or Adjudication record contains. Written only in the main session, never by a subagent — a subagent cannot surface an approval prompt, and an Adjudication requires a named human decider (`07-stages.md`, `02-plan.md` §5).

## Schema

`schemas/adjudication.schema.json`. One JSON object per file: `consensus/<id>.json` (mechanical) or `adjudications/<id>.json` (human).

## Two kinds — do not conflate them

- **`kind: "consensus-run"`** — the mechanical output of a K-pass ensemble: union of candidates, partitioned into `found-by-all` / `found-by-some` / `found-by-one`. Re-executable; `decided_by` may name the process, not necessarily a person.
- **`kind: "adjudication"`** — a human decision over a Consensus Run's output (or over a boundary proposal, or a Divergence classification). `decided_by` **must** be a human identity. An agent name here is a schema violation, not a shortcut — the schema itself rejects the fixed v1 agent roster in this field when `kind` is `"adjudication"`. Only supersedable, never re-executable.

## Required fields

`id` (`ADJ-NNNN`), `stage` (0–8), `k`, `candidates` (each with `candidate_id`, `found_by`, `decision`), `decided_by`, `decided_at`.

## Content obligations

Every candidate's `partition` should be set (`all`/`some`/`one`) so `scripts/status-report.py`'s agreement distribution is meaningful. Every candidate's `decision` (`accept`/`reject`/`triage`) needs a `rationale` when it is not a straightforward accept — especially anything found-by-one, which Constitution C6 requires to be inspected, not auto-accepted or auto-rejected.

## Behavior-ID / artifact citation

`candidates[].candidate_id` should be the ID of the thing being adjudicated (a Behavior ID, a Divergence ID, a boundary-proposal identifier) so the record is traceable back to what it decided.

## Unknowns

If a candidate's evidence is too thin to decide confidently, use `"decision": "triage"` with a rationale explaining what more is needed — do not force `accept`/`reject` prematurely.

## Minimal worked example

```json
{
  "id": "ADJ-0012",
  "stage": 2,
  "k": 3,
  "framings": ["by-routes", "by-tests", "by-call-sites"],
  "candidates": [
    { "candidate_id": "CTX-Ordering", "found_by": ["by-routes", "by-tests"], "partition": "some", "decision": "accept", "rationale": "linguistic boundary holds; coupling data supports the split" }
  ],
  "kind": "adjudication",
  "decided_by": "Jane Doe",
  "decided_at": "2026-08-01T15:00:00Z",
  "agreement_rate": 0.82
}
```
