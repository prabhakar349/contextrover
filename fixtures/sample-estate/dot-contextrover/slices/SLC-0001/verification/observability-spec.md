# Observability Spec — SLC-0001 Order placement

Per `skills/observability-spec/`.

## Per-Behavior signal

- **BHV-0004** (rejects non-positive quantity) — metric: count of `POST /orders` responses with status 400 and error `quantity must be positive`. Healthy: low, steady rate proportional to bad client input. Broken: a spike (client-side regression upstream) or the metric going to zero while order volume is normal (validation silently bypassed).
- **BHV-0001** (publishes order.created) — metric: count of `order.created` publish attempts vs. count of successful `POST /orders 201` responses. These two counts diverging is the signal that matters most here, since the legacy `publish_order_created` is currently a documented no-op (BHV-0001 evidence) — the new implementation's whole point is closing that gap, and this metric is what proves it did.

## Failure-path alerts (BHV-0004 is the only failure_path: true Behavior in this Slice)

Alert if the 400-rejection rate for `POST /orders` exceeds a threshold sustained over 15 minutes — could indicate a client-side regression, not just normal bad input.

## Async delivery signals (IFC-ASYNC-0001, order.created)

- Consumer lag for billing-svc's consumer group.
- DLQ depth (none configured per `inventory/redaction-policy.json`/`interfaces.json` evidence — flag if one appears, since that means retries are failing silently).
- No ordering-violation detection needed: `ordering_guarantee: "per-partition"` with partition key `id` means no cross-order ordering claim is being made to violate.

## Comparison-period signals (Stage 8 shadow/canary for CTX-0001)

Diff rate on: whether `order.created` was actually published (given the legacy no-op gap, the new system publishing where the old one silently didn't is an *expected*, adjudicated difference — must be excluded from the diff-rate calculation as a known Defect, not counted as a false positive).
