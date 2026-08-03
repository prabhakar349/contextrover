---
name: divergence-register
description: Defines the content and structure of the Divergence Register — places where two or more services disagree about the same concept. Reference when assembling or reviewing inventory/divergences.json.
---

# Divergence Register

Defines what a Divergence record contains. Does not define how to detect divergences — that is `agents/divergence-detector.md`'s job. Classification is a human Adjudication at Stage 2, never this skill's or any agent's call.

## Schema

`schemas/divergence.schema.json`. One JSON object per divergence; `inventory/divergences.json` is a JSON array of these.

## Required fields

`id` (`DVG-NNNN`), `concept` (the single concept in disagreement — one concept per record, not a bundle), `variants` (≥2, each naming `service`, `behavior_id`, `description`), `evidence`.

## Classification obligations (Stage 2)

`classification` starts absent or `"unclassified"` at Stage 1 detection. By the Stage 2 gate it must be one of `policy` / `false-cognate` / `defect` — a divergence left `unclassified` past Stage 2 is a gate failure (`trace-lint.py --stage 2`). Each classification needs a `decision_owner` and `decided_at`; that pairing is the record's own embedded Adjudication trail (it does not need a separate `adjudications/*.json` file — the fields live directly on the Divergence record).

- **policy** — model as explicit domain variation. Populate `driving_dimension` (channel, product, tenant, mechanism) and consider whether it belongs in a `variation-policy` record too.
- **false-cognate** — the variants belong to different bounded contexts; they only look like one concept.
- **defect** — preserve behavior, log it, fix separately after migration. Do not silently reconcile a defect into "correct" behavior during migration — that is an unadjudicated behavioral change.

## Behavior-ID citation

Every variant cites the `behavior_id` that exhibits it. A variant with no Behavior ID is not yet evidenced enough to register.

## Unknowns

If you can see two services disagree but cannot yet pin the concept down precisely, register it anyway with your best description and note the uncertainty in `evidence` (Constitution C10) — do not wait for certainty to record a candidate.

## Minimal worked example

```json
{
  "id": "DVG-0003",
  "concept": "order status values",
  "variants": [
    { "service": "orders-svc", "behavior_id": "BHV-0011", "description": "uses PENDING/CONFIRMED/CANCELLED" },
    { "service": "billing-svc", "behavior_id": "BHV-0057", "description": "uses OPEN/CLOSED" }
  ],
  "classification": "false-cognate",
  "decision_owner": "Jane Doe",
  "decided_at": "2026-08-01T12:00:00Z",
  "rationale": "billing's OPEN/CLOSED tracks invoice lifecycle, not order lifecycle — different concept entirely",
  "evidence": [ { "source": "code", "locator": "orders/status.py:5" } ]
}
```
