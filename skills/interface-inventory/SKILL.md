---
name: interface-inventory
description: Defines the content and structure of the Interface Inventory — synchronous endpoints and asynchronous streams, published and consumed. Reference when assembling or reviewing inventory/interfaces.json.
---

# Interface Inventory

Defines what an Interface record contains. Does not define how to discover interfaces — that is the discovery agents' job (`agents/sync-surface-extractor.md`, `agents/async-surface-extractor.md`), reading from the language pack (seam S3.2).

## Schema

`schemas/interface.schema.json`. One JSON object per interface; `inventory/interfaces.json` is a JSON array of these.

## Required fields

`id` (`IFC-SYNC-NNNN` or `IFC-ASYNC-NNNN`), `kind` (`sync` | `async-published` | `async-consumed`), `name`, `owning_service`, `evidence` (non-empty).

## Content obligations by kind

- **sync** — populate the `sync` object: method, path, request/response schema if resolvable, observed status codes.
- **async-published** / **async-consumed** — populate the `async` object in full: topic, payload schema, schema registry ID if any, partition key, ordering guarantee, delivery semantics, idempotency key, retry policy, DLQ, retention. Endpoint-only inventories are a documented failure of prior art (REQ-01) — async fields are not optional decoration.
- **consumers** — every entry needs `identifier`, `evidence_source`, `confidence`. `consumers_complete` defaults to `false` for async interfaces and must stay `false` unless both schema-registry evidence and consumer-group evidence support `true`. Do not set it `true` on partial evidence.

## Behavior-ID citation

An Interface does not cite Behaviors directly — Behaviors cite Interfaces (`behavior.interfaces[]`). The traceability spine runs Behavior → Interface, not the reverse; do not add a `behaviors` field to an Interface record.

## Unknowns

Any field you cannot determine is `"unknown"` where the schema has that enum value, or omitted with the gap noted in `evidence` — never a guess (Constitution C10).

## Minimal worked example

```json
{
  "id": "IFC-ASYNC-0007",
  "kind": "async-published",
  "name": "order.created",
  "owning_service": "orders-svc",
  "protocol": "kafka",
  "async": {
    "topic": "order.created",
    "partition_key": "order_id",
    "ordering_guarantee": "per-partition",
    "delivery": "at-least-once",
    "dlq": "order.created.dlq"
  },
  "consumers": [
    { "identifier": "billing-svc", "evidence_source": "consumer-group", "confidence": "high" }
  ],
  "consumers_complete": false,
  "evidence": [ { "source": "code", "locator": "orders/publisher.py:41" } ]
}
```
