---
name: variation-policy
description: Defines the content and structure of a Variation Policy — formalizing a Divergence classified 'policy' as explicit, intentional domain variation. Reference when assembling or reviewing model/variation-policy.json.
---

# Variation Policy

Defines what a Variation Policy record contains. A Variation Policy exists only for Divergences classified `policy` at Stage 2 — it is where "this is deliberate, not a defect" gets modeled explicitly rather than left as a footnote on the Divergence record.

## Schema

`schemas/variation-policy.schema.json`. One JSON object per variation axis; `model/variation-policy.json` is a JSON array of these.

## Required fields

`id` (`VAR-NNNN`), `context` (`CTX-NNNN`), `driving_dimension` (what actually varies: channel, product, tenant, mechanism — name the real axis, not a vague "it depends"), `variants` (≥1, each with `value` and `description`), `evidence`.

## Content obligations

Link back to the Divergence(s) this formalizes via `divergences[]` — a Variation Policy that doesn't trace to at least one `policy`-classified Divergence is either premature or duplicating something that belongs on the Divergence record directly. Record `decided_by` and `decided_at` — this is a human decision, carried forward from the Stage 2 Adjudication, not a re-derivation.

## Behavior-ID citation

Each variant should cite the `behavior_id` that exhibits it, exactly like a Divergence variant does — the traceability spine does not stop at classification.

## Unknowns

If the driving dimension is suspected but not confirmed, say so in `rationale` rather than asserting a dimension you can't support — a wrong driving dimension here misleads every future variant added under it.

## Minimal worked example

```json
{
  "id": "VAR-0001",
  "context": "CTX-0001",
  "driving_dimension": "channel",
  "divergences": ["DVG-0009"],
  "variants": [
    { "value": "web", "description": "requires email confirmation before order placement", "behavior_id": "BHV-0031" },
    { "value": "in-store", "description": "no confirmation step; cashier authorizes", "behavior_id": "BHV-0032" }
  ],
  "decided_by": "Jane Doe",
  "decided_at": "2026-08-01T15:00:00Z",
  "rationale": "confirmed with product: channel-specific by design, not an oversight",
  "evidence": [ { "source": "code", "locator": "orders/checkout.py:20" } ]
}
```
