from flask import Flask, request, jsonify
import json
import bcrypt
import os

app = Flask(__name__)

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
        return jsonify({"message": "Chybí jméno nebo heslo"}), 400

    users = load_users()

    if username in users:
        return jsonify({"message": "Uživatel již existuje"}), 409

    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    users[username] = hashed_pw
    save_users(users)

    return jsonify({"message": "Uživatel úspěšně registrován"}), 201

@app.route("/", methods=["GET"])
def index():
    return "Backend běží"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

