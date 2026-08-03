# Decommission Checklist — CTX-0001 (Ordering)

- [x] All Slices in this Context `Accepted` (SLC-0001 only — `slices/SLC-0001/slice.json`)
- [x] Shadow, canary, and progressive-cutover steps complete with diff rate under threshold at each step (`cutover-plan.json`)
- [x] IFC-SYNC-0003 (`POST /orders`, legacy) — zero traffic for 47 days, `retirement.json` status `retired`
- [x] IFC-ASYNC-0001 (`order.created`, legacy publisher) — zero traffic for 47 days, `retirement.json` status `retired`
- [x] Known consumer (`web-app`) confirmed migrated to the new `PlaceOrder` contract
- [x] Known consumer (`billing-svc`) confirmed migrated to the new `OrderPlaced`-backed contract
- [x] Legacy `orders-svc` deployment decommissioned
- [x] Observability: new-system dashboards live before legacy teardown (`slices/SLC-0001/verification/observability-spec.md`)

Sunset authority: Jane Doe (per `intake.json.governance.sunset_authority`).
