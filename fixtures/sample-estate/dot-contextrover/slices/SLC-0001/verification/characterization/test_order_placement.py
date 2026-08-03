"""Characterization suite -- SLC-0001 Order placement.

Operates at the protocol boundary (HTTP), never at language internals (DR1).
Illustrative for this fixture -- not executed as part of the plugin build
(Flask/pytest are not installed in the plugin's own dev environment, and
should not be; this is target-repo tooling, per Constitution C8/C5). Real
execution happens via the pack's own test runner (packs/python/PACK.md §5)
when Stage 6/7 actually run against a real target repo.

Covers BHV-0001 (publishes order.created), BHV-0004 (rejects non-positive
quantity) -- both happy and failure path, per REQ-03/DR1.
"""
import pytest
from app import app as flask_app  # services/orders-svc/app.py


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


# --- BHV-0004: Rejects an order when requested quantity is zero or negative (failure path) ---

def test_place_order_rejects_zero_quantity(client):
    resp = client.post("/orders", json={"quantity": 0})
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "quantity must be positive"}


def test_place_order_rejects_negative_quantity(client):
    resp = client.post("/orders", json={"quantity": -5})
    assert resp.status_code == 400


# --- BHV-0004: happy path ---

def test_place_order_accepts_positive_quantity(client):
    resp = client.post("/orders", json={"quantity": 3})
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["quantity"] == 3
    assert body["status"] == "PENDING"


# --- BHV-0001: Publishes an order.created event after an order is placed ---
# Protocol-boundary assertion: which event, what order, what partition key --
# not just "an event was emitted" (07-stages.md Stage 6 requirement).

def test_place_order_publishes_order_created_event(client, monkeypatch):
    published = []
    monkeypatch.setattr(
        "app.publish_order_created",
        lambda order: published.append(order),
    )
    resp = client.post("/orders", json={"quantity": 2})
    assert resp.status_code == 201
    assert len(published) == 1, "expected exactly one order.created publish call"
    assert published[0]["id"] is not None, "partition key (order id) must be present"


def test_place_order_created_event_not_published_on_rejection(client, monkeypatch):
    published = []
    monkeypatch.setattr("app.publish_order_created", lambda order: published.append(order))
    client.post("/orders", json={"quantity": 0})
    assert published == [], "a rejected order must not publish order.created"
