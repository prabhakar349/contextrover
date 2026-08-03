"""orders-svc — trivial Flask-style service. Fixture only, not organization-specific."""
from flask import Flask, request, jsonify

app = Flask(__name__)

# order.status lifecycle: PENDING -> CONFIRMED -> CANCELLED (order lifecycle, not invoice lifecycle)
ORDER_STATUSES = ["PENDING", "CONFIRMED", "CANCELLED"]


@app.route("/orders", methods=["POST"])
def place_order():
    body = request.get_json()
    quantity = body.get("quantity", 0)
    if quantity <= 0:
        # BHV: rejects an order when requested quantity is zero or negative
        return jsonify({"error": "quantity must be positive"}), 400

    order = {"id": "ord-1", "quantity": quantity, "status": "PENDING"}
    publish_order_created(order)
    return jsonify(order), 201


def publish_order_created(order):
    """Publishes to topic 'order.created'. Partition key: order id. At-least-once delivery."""
    # kafka_producer.send(topic="order.created", key=order["id"], value=order)
    pass
