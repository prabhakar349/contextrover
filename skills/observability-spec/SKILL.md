---
name: observability-spec
description: Defines the content and structure of a Slice's observability specification. Reference when assembling or reviewing slices/<id>/verification/observability-spec.md.
---

# Observability Spec

Defines what the observability spec must cover, so day-zero observability is actually provisioned (REQ-46) rather than added after the first incident.

## Schema anchor

`schemas/behavior.schema.json`. What to monitor is derived directly from the Slice's Behaviors, with particular weight on `failure_path: true` Behaviors — those are exactly the paths that need an alert, not just a log line, because they are the ones a migration is most likely to get subtly wrong.

## Required content

1. **Per-Behavior signal** — for each Behavior in the Slice, what a healthy execution looks like and what a broken one looks like observably (a metric, a log pattern, a trace span).
2. **Failure-path alerts** — every `failure_path: true` Behavior needs an explicit alert condition, not just inclusion in a general error-rate dashboard.
3. **Async delivery signals** — for each async Interface in scope: consumer lag, DLQ depth, and ordering-violation detection where the Interface declares an ordering guarantee (`interface.async.ordering_guarantee`) worth monitoring for violation.
4. **Comparison-period signals** — during Stage 8 shadow and canary, what diff-rate and SLO signals this Slice's Context needs (feeds `contexts/<id>/cutover-plan.json`).

## Behavior-ID citation

Each monitored signal should name the Behavior ID(s) it is watching over — an observability spec that can't say which Behavior an alert protects is not yet actionable when it fires.

## What this skill does not cover

The actual provisioning of dashboards or alerts in a specific observability platform — REQ-45 defers observability *connectors* to v2; this spec is what to provision, written so a human or a future connector can act on it, platform-agnostic.
