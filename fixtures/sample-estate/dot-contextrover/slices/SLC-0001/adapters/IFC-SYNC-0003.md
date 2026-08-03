# Adapter — IFC-SYNC-0003 (`POST /orders`)

Owner: Ordering team

Anticorruption Layer translating the legacy `POST /orders` request/response shape to the new `PlaceOrder` command and `Order` aggregate. Legacy status codes (201/400) preserved at the boundary.
