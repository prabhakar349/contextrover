---
name: characterization-suite
description: Defines the content and structure of a Slice's characterization test suite. Reference when assembling or reviewing slices/<id>/verification/characterization/*.
---

# Characterization Suite

Defines what the characterization suite must cover. Does not define how tests are generated or which language-specific harness conventions apply — that is Stage 6's `packs/<language>/PACK.md` territory (Constitution C8); this skill governs coverage obligations, which are language-independent.

## Schema anchor

`schemas/coverage.schema.json` (`slices/<id>/verification/coverage.json`) is the measurable output of this suite — `denominator`, `total`, `covered`, `passing`, `happy_path`, and `failure_path` are computed directly from what the suite actually exercises. If `coverage.json` under-reports, the suite is incomplete, not the report wrong.

## Coverage obligations (REQ-05, REQ-12, `07-stages.md` Stage 6)

- Operates at the **protocol boundary** — HTTP and event payloads — never at language internals (DR1). A unit test pinning an internal function is the wrong layer for this suite entirely.
- Every Behavior in the Slice needs at least one characterization test; **failure-path Behaviors are covered and reported separately from happy-path** (`coverage.json.failure_path`) — a suite that looks complete while skipping failure paths is the characteristic silent failure this method exists to catch.
- For async Behaviors: assert not just that an event was emitted, but **which** event, in **what order**, and with **what partition key**.
- Redaction Policy verdict must be `GO` for every Interface this suite compares against (`inventory/redaction-policy.json`) — a `NO-GO` interface cannot be meaningfully characterized yet; that gate exists precisely to stop a suite that would compare noise.

## Behavior-ID citation

Every test should be traceable to the Behavior ID(s) it covers — this is what makes `covers` edges in the graph meaningful (`scripts/build-graph.py`) and what `scripts/graph-query.py coverage` can check.

## The harness freeze

Once this suite passes the Stage 6 gate, its hash is written to `harness.lock` (`07-stages.md` §2). The suite may not change silently during Stage 7 — any change voids the gate and requires a recorded re-approval by the QA/SRE approver.

## What this skill does not cover

Adversarial gap-finding against the suite — that is `agents/test-adversary.md`'s job, feeding back into what this suite must add before it is frozen.
