# Adapter — IFC-ASYNC-0001 (`order.created`)

Owner: Ordering team

Anticorruption Layer translating the `OrderPlaced` domain event into the legacy `order.created` Kafka payload shape. Partition key (`id`) preserved so billing-svc's consumer ordering is unaffected by the migration.
