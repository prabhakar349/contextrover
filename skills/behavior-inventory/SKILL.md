---
name: behavior-inventory
description: Defines the content and structure of the Behavior Inventory — the unit of traceability for the whole method. Reference when assembling or reviewing inventory/behaviors.json.
---

# Behavior Inventory

Defines what a Behavior record contains. Does not define how to extract behaviors — that is `agents/behavior-extractor.md`'s job, and identity resolution across runs is `scripts/resolve-identity.py`'s job (REQ-31a), never an agent's.

## Schema

`schemas/behavior.schema.json`. One JSON object per behavior; `inventory/behaviors.json` is a JSON array of these.

## Required fields

`id` (`BHV-NNNN`), `summary` (≥10 characters, one atomic fact, not a module summary), `source_services` (≥1), `evidence` (≥1), `confidence`.

## Content obligations

- `kind` classifies the behavior: validation, calculation, routing, state-transition, error-mapping, side-effect, emission, or other.
- `failure_path: true` for anything describing failure, timeout, or partial-completion — these are under-represented by default (`01-spec.md` DR1) and must be marked, not left to inference.
- `confidence: "unknown"` requires a `reason`. Do not default to `"medium"` to avoid writing a reason.
- `status` defaults to `"confirmed"`. `"unconfirmed"` is set only by `scripts/resolve-identity.py` when a previously-seen Behavior is absent from the latest run — never set by hand.

## Behavior-ID citation

A Behavior is the thing everything else cites, not the other way around. Its own `spec_clauses` and `tests` fields, once populated downstream, are how coverage becomes computable (REQ-12): % of Behavior IDs with a passing characterization test.

## Unknowns

An undeterminable field is `"confidence": "unknown"` with a `reason` — never omitted, never guessed (REQ-09, Constitution C10).

## Minimal worked example

```json
{
  "id": "BHV-0042",
  "summary": "Rejects an order when requested quantity is zero or negative",
  "source_services": ["orders-svc"],
  "interfaces": ["IFC-SYNC-0001"],
  "kind": "validation",
  "failure_path": true,
  "evidence": [ { "source": "code", "locator": "orders/validate.py:42" } ],
  "confidence": "high"
}
```
