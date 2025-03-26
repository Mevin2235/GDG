from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import bcrypt

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# MongoDB Configuration
client = MongoClient("mongodb://127.0.0.1:27017/")
db = client['ai_teacher_assistant']
users_collection = db['users']
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    user_type = data.get('userType')

    print(f"📥 Signup attempt - Email: {email}, User Type: {user_type}")

    if not email or not password or not user_type:
        print("❌ Signup failed: Missing fields")
        return jsonify({'message': '❌ All fields are required!'}), 400

    existing_user = users_collection.find_one({'email': email})
    if existing_user:
        print("⚠️ Signup failed: User already exists")
        return jsonify({'message': '⚠️ User already exists!'}), 409

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    new_user = {
        'email': email,
        'password': hashed_password,
        'userType': user_type
    }

    users_collection.insert_one(new_user)
    print(f"✅ Signup successful for user: {email}")

    return jsonify({'message': '✅ Account created successfully!'}), 201

# ==========================
# 🔑 User Login
# ==========================
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    print(f"🔐 Login attempt - Email: {email}")

    if not email or not password:
        print("❌ Login failed: Missing fields")
        return jsonify({'message': '❌ Email and password are required!'}), 400

    user = users_collection.find_one({'email': email})
    if not user:
        print("❌ Login failed: User not found")
        return jsonify({'message': '❌ User not found!'}), 404

    if bcrypt.checkpw(password.encode('utf-8'), user['password']):
        user_type = user['userType']
        redirect_page = 'student_dashboard.html' if user_type == 'student' else 'home.html'

        print(f"✅ Login successful! Redirecting to: {redirect_page}")

        return jsonify({
            'message': '✅ Login successful!',
            'userType': user_type,
            'redirectPage': redirect_page
        }), 200
    else:
        print("❌ Login failed: Incorrect password")
        return jsonify({'message': '❌ Incorrect password!'}), 401

# ==========================
# Start the Server
# ==========================
if __name__ == '__main__':
    print("🚀 Server is running on http://127.0.0.1:5000/")
    app.run(debug=True, port=5000)
