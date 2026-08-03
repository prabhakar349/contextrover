# Design — SLC-0001 Order placement

## Scope

Context: CTX-0001 (Ordering). Behaviors in scope: BHV-0001, BHV-0004.

## Aggregates

### Order (root: Order)

- Invariant: an Order is never created with a non-positive quantity (BHV-0004). Enforced at the aggregate boundary — quantity is validated before the Order is constructed, not after.
- Invariant: an Order transitions into PENDING at creation and an `order.created` event is emitted for every successfully created Order (BHV-0001). This is what the new API commits to that the legacy handler's commented-out publish call currently does not actually deliver on (BHV-0001 evidence notes the legacy `publish_order_created` is a documented no-op) — the new implementation must genuinely publish, not just declare the intent to.
- Entities: OrderLine. Value objects: Quantity.

## Domain events and commands

- `PlaceOrder` (command, imperative) → `OrderPlaced` (domain event, past tense) on the Order aggregate.
- Policy: when `OrderPlaced`, notify Billing — realized today via the `order.created` topic (IFC-ASYNC-0001).

## Legacy adapter approach

- **IFC-SYNC-0003** (`POST /orders`) — Anticorruption Layer at the boundary; the new Order aggregate's `PlaceOrder` command is invoked from a thin adapter translating the legacy request/response shape. Owner: see `adapters/IFC-SYNC-0003.md`.
- **IFC-ASYNC-0001** (`order.created`) — Adapter translates `OrderPlaced` into the legacy `order.created` payload shape, preserving the partition key (`id`) so existing consumers (billing-svc) see no ordering change. Owner: see `adapters/IFC-ASYNC-0001.md`.

## Open questions

- The legacy `publish_order_created` function's Kafka call is commented out (BHV-0001 evidence) — confirm with the Ordering team whether this is fixture stubbing or a real gap in the estate being modernized, since it changes what "preserving behavior" means for this Behavior specifically: preserving a no-op, or fixing it as an adjudicated Defect.
