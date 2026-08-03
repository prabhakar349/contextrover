"""Consumer-driven contract test -- IFC-ASYNC-0001 (order.created).

Asserts the published contract billing-svc's consumeOrderCreated (the known
consumer, per inventory/interfaces.json) actually depends on: payload shape,
partition key. Illustrative for this fixture, not executed (see
test_order_placement.py's module docstring for why).
"""
import pytest
from app import app as flask_app


REQUIRED_FIELDS = {"id", "quantity", "status"}


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def test_order_created_payload_has_required_fields(client, monkeypatch):
    published = []
    monkeypatch.setattr("app.publish_order_created", lambda order: published.append(order))
    client.post("/orders", json={"quantity": 1})
    assert REQUIRED_FIELDS.issubset(published[0].keys())


def test_order_created_partition_key_is_order_id(client, monkeypatch):
    published = []
    monkeypatch.setattr("app.publish_order_created", lambda order: published.append(order))
    client.post("/orders", json={"quantity": 1})
    # partition_key: "id" per inventory/interfaces.json IFC-ASYNC-0001.async.partition_key
    assert "id" in published[0]
