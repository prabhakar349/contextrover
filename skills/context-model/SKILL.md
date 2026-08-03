---
name: context-model
description: Defines the content and structure of the Modeled Context and Context Map — the Stage 2 Strategic Design output. Reference when assembling or reviewing model/contexts.json and model/context-map.json.
---

# Context Model

Defines what a Context record and a Context Map relationship contain. Does not define how boundaries are chosen — that is a human Adjudication informed by `agents/boundary-proposer.md`'s proposals, never this skill's call (Constitution C9, DR2).

## Schemas

`schemas/context.schema.json` (`model/contexts.json`, one array item per Context) and `schemas/context-map.schema.json` (`model/context-map.json`, one array item per relationship between two Contexts).

## Required fields — Context

`id` (`CTX-NNNN`), `name`, `aggregate_roots` (≥1 — a Context with no aggregate root is not yet a modeled context, it is a grouping heuristic that hasn't earned the name), `state`, `evidence`. `aggregate_roots` at this stage are candidate names only, named per `knowledge/ddd-reference.md` §2 (Vernon's rules — an aggregate exists to enforce an invariant; if nobody can name the rule it enforces, it is not yet a real candidate). Full invariants are not modeled until Tactical Design (Stage 5, `skills/tactical-model/`).

## Required fields — Context Map relationship

`context_a`, `context_b`, `pattern` (one of the eight standard DDD relationship patterns — `knowledge/ddd-reference.md` §1.3), `evidence`. Every pair of Contexts that communicate needs exactly one named pattern; leaving it unnamed is how integration debt accumulates. For a heritage system, the default is `anticorruption-layer` — never merge a legacy context into a new one "to clean it up."

## Behavior-ID citation

A Context does not cite Behaviors directly. Behaviors cite their Context (`behavior.context`), and the Stage 2 gate requires every Behavior to map to exactly one Context (`trace-lint.py --stage 2`). A Context with zero Behaviors pointing to it is an orphan (`scripts/graph-query.py orphans`).

## Content obligations

Populate `subdomain_type` (core/supporting/generic — `knowledge/ddd-reference.md` §1.1) so effort investment decisions are visible later. Populate `ubiquitous_language` as the model stabilizes — this is what makes the context legible to someone who has not sat in the room.

## Unknowns

Where a boundary is genuinely undecided, the Context should not exist yet — record it as a candidate in the boundary-proposer's output, not as a half-committed Context record.

## Minimal worked example

```json
{ "id": "CTX-0001", "name": "Ordering", "subdomain_type": "core",
  "aggregate_roots": ["Order"], "state": "Approved",
  "evidence": [ { "source": "code", "locator": "orders/" } ] }
```

```json
{ "context_a": "CTX-0001", "context_b": "CTX-0002", "pattern": "anticorruption-layer",
  "upstream": "CTX-0002", "rationale": "CTX-0002 is the legacy billing system; Ordering translates at the edge",
  "evidence": [ { "source": "code", "locator": "orders/billing_adapter.py:1" } ] }
```
