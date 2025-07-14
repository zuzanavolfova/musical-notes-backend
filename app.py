from flask_cors import CORS
from flask import Flask, request, jsonify
import bcrypt
import os
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
CORS(app)

MONGO_URI = os.getenv("MONGO_URI", "<tvůj_connection_string>")
client = MongoClient(MONGO_URI)
db = client["musical_notes_db"]
users_col = db["users"]

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Missing username or password"}), 400

    if users_col.find_one({"username": username}):
        return jsonify({"message": "User already exists"}), 409

    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    users_col.insert_one({
        "username": username,
        "password": hashed_pw,
        "statistics": []
    })

    return jsonify({"message": "User registered successfully"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Missing username or password"}), 400

    user = users_col.find_one({"username": username})
    if not user:
        return jsonify({"message": "User not found"}), 404

    if bcrypt.checkpw(password.encode(), user["password"]):
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"message": "Incorrect password"}), 401

@app.route("/save-statistics", methods=["POST"])
def save_statistics():
    data = request.get_json() or {}
    username = data.get("userName")
    good = data.get("goodAnswers")
    wrong = data.get("wrongAnswers")

    if not username or good is None or wrong is None:
        return jsonify({"message": "Missing required fields"}), 400

    ts = data.get("timeStamp") or datetime.utcnow().isoformat()
    stat = {"goodAnswers": good, "wrongAnswers": wrong, "timeStamp": ts}

    result = users_col.update_one(
        {"username": username},
        {"$push": {"statistics": stat}}
    )
    if result.matched_count == 0:
        return jsonify({"message": "User not found"}), 404

    return jsonify({"message": "Statistics saved"}), 201

@app.route("/get-statistics", methods=["GET"])
def get_statistics():
    username = request.args.get("userName")
    if not username:
        return jsonify({"message": "Missing userName parameter"}), 400

    user = users_col.find_one({"username": username}, {"statistics": 1})
    if not user:
        return jsonify({"message": f"User '{username}' not found"}), 404

    return jsonify({"statistics": user.get("statistics", [])}), 200

@app.route("/users", methods=["GET"])
def get_users():
    names = [u["username"] for u in users_col.find({}, {"_id": 0, "username": 1})]
    return jsonify({"users": names}), 200

@app.route("/", methods=["GET"])
def index():
    return "Backend is running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)