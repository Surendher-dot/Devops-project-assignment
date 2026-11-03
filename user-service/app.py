from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app, group_by="endpoint")
USERS = {
    1: {"id": 1, "name": "Surya", "email": "surya@example.com"},
    2: {"id": 2, "name": "Ravi", "email": "ravi@example.com"},
}

@app.get("/health")
def health():
    return jsonify(status="healthy", service="user-service")

@app.get("/users")
def get_users():
    return jsonify(list(USERS.values()))

@app.get("/users/<int:user_id>")
def get_user(user_id):
    user = USERS.get(user_id)
    return (jsonify(user), 200) if user else (jsonify(error="User not found"), 404)

@app.post("/users")
def create_user():
    data = request.get_json(silent=True) or {}
    if not data.get("name") or not data.get("email"):
        return jsonify(error="Both name and email are required"), 400
    new_id = max(USERS, default=0) + 1
    user = {"id": new_id, "name": data["name"], "email": data["email"]}
    USERS[new_id] = user
    return jsonify(user), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
