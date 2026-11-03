import os
import requests
from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app, group_by="endpoint")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:5001")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:5002")
ORDERS = {}
NEXT_ORDER_ID = 1

@app.get("/health")
def health():
    return jsonify(status="healthy", service="order-service")

@app.get("/orders")
def get_orders():
    return jsonify(list(ORDERS.values()))

@app.get("/orders/<int:order_id>")
def get_order(order_id):
    order = ORDERS.get(order_id)
    return (jsonify(order), 200) if order else (jsonify(error="Order not found"), 404)

@app.post("/orders")
def create_order():
    global NEXT_ORDER_ID
    data = request.get_json(silent=True) or {}
    user_id, product_id = data.get("user_id"), data.get("product_id")
    quantity = data.get("quantity", 1)
    if not isinstance(user_id, int) or not isinstance(product_id, int):
        return jsonify(error="user_id and product_id must be integers"), 400
    if not isinstance(quantity, int) or quantity < 1:
        return jsonify(error="quantity must be a positive integer"), 400
    try:
        u = requests.get(f"{USER_SERVICE_URL}/users/{user_id}", timeout=3)
        p = requests.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}", timeout=3)
    except requests.RequestException:
        return jsonify(error="A dependent service is unavailable"), 503
    if u.status_code == 404:
        return jsonify(error="User does not exist"), 404
    if p.status_code == 404:
        return jsonify(error="Product does not exist"), 404
    if not u.ok or not p.ok:
        return jsonify(error="Could not validate order details"), 502
    user, product = u.json(), p.json()
    order = {
        "id": NEXT_ORDER_ID, "user": user, "product": product,
        "quantity": quantity, "total": round(product["price"] * quantity, 2),
        "status": "created"
    }
    ORDERS[NEXT_ORDER_ID] = order
    NEXT_ORDER_ID += 1
    return jsonify(order), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)
