from flask_cors import CORS
from flask import Flask, request, jsonify
import json
import bcrypt
import os

app = Flask(__name__)
CORS(app) 

DATA_FILE = "users.json"
def load_users():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(DATA_FILE, "w") as f:
        json.dump(users, f, indent=2)

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Missing username or password"}), 400

    users = load_users()

    if username in users:
        return jsonify({"message": "User already exists"}), 409

    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    users[username] = {
        "password": hashed_pw,
        "statistics": []
    }
    save_users(users)

    return jsonify({"message": "User registered successfully"}), 201

@app.route("/save-statistics", methods=["POST"])
def save_statistics():
    data = request.get_json()
    username = data.get("userName")
    goodAnswers = data.get("goodAnswers")
    wrongAnswers = data.get("wrongAnswers")
    timeStamp = data.get("timeStamp") or None

    if not username or goodAnswers is None or wrongAnswers is None:
        return jsonify({"message": "Missing required fields"}), 400

    users = load_users()
    if username not in users:
        return jsonify({"message": "User not found"}), 404

    if not timeStamp:
        from datetime import datetime
        timeStamp = datetime.utcnow().isoformat()

    stat = {
        "goodAnswers": goodAnswers,
        "wrongAnswers": wrongAnswers,
        "timeStamp": timeStamp
    }
    users[username].setdefault("statistics", []).append(stat)
    save_users(users)
    return jsonify({"message": "Statistics saved"}), 201

@app.route("/users", methods=["GET"])
def get_users():
    users = load_users()
    return jsonify(list(users.keys()))

@app.route("/", methods=["GET"])
def index():
    return "Backend is runnig"

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Missing username or password"}), 400

    users = load_users()
    user = users.get(username)

    if not user:
        return jsonify({"message": "User not found"}), 404

    hashed_pw = user["password"]

    if bcrypt.checkpw(password.encode(), hashed_pw.encode()):
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"message": "Incorrect password"}), 401

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)