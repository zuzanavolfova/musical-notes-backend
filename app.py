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
    if users_col is None:
        return jsonify({"message": "Database connection failed"}), 503
        
    try:
        print("=== REGISTER ENDPOINT CALLED ===")
        
        data = request.get_json()
        print(f"Request data: {data}")
        
        if not data:
            print("No JSON data received")
            return jsonify({"message": "No JSON data provided"}), 400
            
        username = data.get("username")
        password = data.get("password")
        
        print(f"Username: {username}, Password length: {len(password) if password else 0}")

        if not username or not password:
            print("Missing username or password")
            return jsonify({"message": "Missing username or password"}), 400

        print("Checking if user already exists...")
        existing_user = users_col.find_one({"username": username})
        if existing_user:
            print(f"User {username} already exists")
            return jsonify({"message": "User already exists"}), 409

        print("Hashing password...")
        try:
            password_bytes = password.encode('utf-8')
            print(f"Password converted to bytes: {len(password_bytes)} bytes")
            
            salt = bcrypt.gensalt()
            print(f"Salt generated: {salt}")
            
            hashed_bytes = bcrypt.hashpw(password_bytes, salt)
            print(f"Password hashed: {len(hashed_bytes)} bytes")
            
            hashed_pw = hashed_bytes.decode('utf-8')
            print(f"Hash converted to string: {len(hashed_pw)} characters")
            
        except Exception as hash_error:
            print(f"Error hashing password: {hash_error}")
            print(f"Error type: {type(hash_error).__name__}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return jsonify({"message": "Password hashing failed"}), 500

        print("Creating user document...")
        user_doc = {
            "username": username,
            "password": hashed_pw,
            "statistics": []
        }
        print(f"User document created - username: {user_doc['username']}, password length: {len(user_doc['password'])}")

        print("Inserting user into database...")
        try:
            result = users_col.insert_one(user_doc)
            print(f"User inserted with ID: {result.inserted_id}")
        except Exception as db_error:
            print(f"Database insertion error: {db_error}")
            print(f"Error type: {type(db_error).__name__}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return jsonify({"message": "Database insertion failed"}), 500

        print("Registration successful!")
        return jsonify({"message": "User registered successfully"}), 201
        
    except Exception as e:
        print(f"=== REGISTER ERROR ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return jsonify({"message": f"Server error: {str(e)}"}), 500

@app.route("/login", methods=["POST"])
def login():
    if users_col is None:
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
    if users_col is None:
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
    if users_col is None:
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
    if users_col is None:
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