from flask_cors import CORS
from flask import Flask, request, jsonify
import bcrypt
import os
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app)

MONGO_URI = os.getenv("MONGO_URI")

try:
    client = MongoClient(
        MONGO_URI,
        tls=True,
        tlsInsecure=True,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000
    )
    db = client["musical_notes_db"]
    users_col = db["users"]
    
    client.admin.command('ping')
    print("MongoDB connection successful")
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    client = None
    db = None
    users_col = None

@app.route("/register", methods=["POST"])
def register():
    if not users_col:
        return jsonify({"message": "Database connection failed"}), 503
        
    try:
        data = request.get_json() or {}
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"message": "Missing username or password"}), 400

        if users_col.find_one({"username": username}):
            return jsonify({"message": "User already exists"}), 409

        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode('utf-8')

        users_col.insert_one({
            "username": username,
            "password": hashed_pw,
            "statistics": []
        })

        return jsonify({"message": "User registered successfully"}), 201
        
    except Exception as e:
        print(f"Register error: {str(e)}")
        return jsonify({"message": f"Server error: {str(e)}"}), 500

@app.route("/login", methods=["POST"])
def login():
    if not users_col:
        return jsonify({"message": "Database connection failed"}), 503
        
    try:
        data = request.get_json() or {}
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"message": "Missing username or password"}), 400

        user = users_col.find_one({"username": username})
        if not user:
            return jsonify({"message": "User not found"}), 404

        stored_password = user["password"].encode('utf-8')
        if bcrypt.checkpw(password.encode(), stored_password):
            return jsonify({"message": "Login successful"}), 200
        else:
            return jsonify({"message": "Incorrect password"}), 401
            
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({"message": f"Server error: {str(e)}"}), 500

@app.route("/save-statistics", methods=["POST"])
def save_statistics():
    if not users_col:
        return jsonify({"message": "Database connection failed"}), 503
        
    try:
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
        
    except Exception as e:
        print(f"Save statistics error: {str(e)}")
        return jsonify({"message": f"Server error: {str(e)}"}), 500

@app.route("/get-statistics", methods=["GET"])
def get_statistics():
    if not users_col:
        return jsonify({"message": "Database connection failed"}), 503
        
    try:
        username = request.args.get("userName")
        if not username:
            return jsonify({"message": "Missing userName parameter"}), 400

        user = users_col.find_one({"username": username}, {"statistics": 1})
        if not user:
            return jsonify({"message": f"User '{username}' not found"}), 404

        return jsonify({"statistics": user.get("statistics", [])}), 200
        
    except Exception as e:
        print(f"Get statistics error: {str(e)}")
        return jsonify({"message": f"Server error: {str(e)}"}), 500

@app.route("/users", methods=["GET"])
def get_users():
    if not users_col:
        return jsonify({"message": "Database connection failed"}), 503
        
    try:
        names = [u["username"] for u in users_col.find({}, {"_id": 0, "username": 1})]
        return jsonify({"users": names}), 200
        
    except Exception as e:
        print(f"Get users error: {str(e)}")
        return jsonify({"message": f"Server error: {str(e)}"}), 500

@app.route("/health", methods=["GET"])
def health_check():
    try:
        if client:
            client.admin.command('ping')
            return jsonify({"status": "healthy", "database": "connected"}), 200
        else:
            return jsonify({"status": "unhealthy", "database": "disconnected"}), 503
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 503

@app.route("/", methods=["GET"])
def index():
    return "Backend is running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)