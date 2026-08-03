# fixtures/sample-estate

A trivial three-service estate used to verify the build end-to-end (T19). **Not organization-specific — invented services, invented data, safe to ship publicly** (Constitution C4).

- `services/orders-svc/` — Python, HTTP, publishes an event
- `services/billing-svc/` — Go, HTTP, consumes that event
- `services/shipping-svc/` — Java, HTTP

## Seeded characteristics

- **Overlapping behavior with a deliberate Divergence** — both `orders-svc` and `billing-svc` have a `status` concept. Orders uses `PENDING/CONFIRMED/CANCELLED` (order lifecycle); Billing uses `OPEN/CLOSED` (invoice lifecycle). Same word, different concept — a `false-cognate` Divergence (`DVG-0001`).
- **One published event stream** — `orders-svc` publishes `order.created`; `billing-svc` consumes it.
- **A seeded orphan / weak-evidence Behavior** — `shipping-svc`'s Behavior (`BHV-0003`) is found by only one of three framings (`by-call-sites`), at medium confidence, and is deliberately left with no Context assigned in the pre-Stage-2 snapshot, to prove `trace-lint.py --stage 2` and `scripts/graph-query.py orphans` both catch it.
- **A genuine near-duplicate** — `by-routes` and `by-tests` each independently found the "creates an invoice" Behavior, worded differently enough (Jaccard ≈ 0.64) to fall under `resolve-identity.py`'s 0.80 merge threshold. Both surface as separate found-by-one candidates in `consensus/CONSENSUS-BEHAVIORS.json`, and the human review recorded in `adjudications/ADJ-0001.json` rejects the duplicate — a realistic demonstration of why the found-by-one review step exists.

## `passes/1/<framing>/`

Raw candidate output for three framings (`by-routes`, `by-tests`, `by-call-sites`), standing in for what the real discovery agents would produce — hand-authored here since dispatching live agents isn't repeatable enough for a checked-in fixture, but shaped exactly like real agent output (interfaces cited by name, not by ID, since no ID exists yet at this stage — `scripts/consensus.py` resolves that).

## `dot-contextrover/`

A committed `.contextrover/`-shaped directory (deliberately **not** named `.contextrover` — that name is gitignored at the plugin-repo level and would never be committed), built by actually running the real pipeline against `passes/1/`:

```
python3 scripts/consensus.py --dir fixtures/sample-estate/dot-contextrover --stage 1
python3 scripts/resolve-identity.py --candidates fixtures/sample-estate/dot-contextrover/passes/1/merged/behaviors.json \
                                     --dir fixtures/sample-estate/dot-contextrover
```

`inventory/`, `model/`, `workstreams.json`, and `slices/` represent the artifact state after Stages 0–3 complete cleanly against this estate. Point any script at it with `--dir fixtures/sample-estate/dot-contextrover`.

Human-in-the-loop steps (the Stage 0 interview, the Stage 1 found-by-one/some review, the Stage 2 boundary/divergence adjudication) are recorded as fixture responses (`intake.json`, `adjudications/*.json`) rather than run unattended — consistent with `07-stages.md`'s own description of those stages as human-led.
