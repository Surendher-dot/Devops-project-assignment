from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app, group_by="endpoint")
PRODUCTS = {
    101: {"id": 101, "name": "Laptop", "price": 55000.0},
    102: {"id": 102, "name": "Headphones", "price": 2500.0},
}

@app.get("/health")
def health():
    return jsonify(status="healthy", service="product-service")

@app.get("/products")
def get_products():
    return jsonify(list(PRODUCTS.values()))

@app.get("/products/<int:product_id>")
def get_product(product_id):
    product = PRODUCTS.get(product_id)
    return (jsonify(product), 200) if product else (jsonify(error="Product not found"), 404)

@app.post("/products")
def create_product():
    data = request.get_json(silent=True) or {}
    name, price = data.get("name"), data.get("price")
    if not name or not isinstance(price, (int, float)) or price <= 0:
        return jsonify(error="A name and positive numeric price are required"), 400
    new_id = max(PRODUCTS, default=100) + 1
    product = {"id": new_id, "name": name, "price": float(price)}
    PRODUCTS[new_id] = product
    return jsonify(product), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
