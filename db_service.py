from pymongo import MongoClient
from datetime import datetime
import os

# MongoDB connection (local or MongoDB Atlas)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/")

# Connect to MongoDB
client = MongoClient(MONGO_URI)

# Select database and collection
db = client["teacher_assistant_db"]
collection = db["graded_results"]

def store_result(filename, grade, feedback, name, register_no, student_class):
    """
    Save the file name, grade, feedback, and student identity fields to MongoDB.
    """
    document = {
        "filename": filename,
        "grade": grade,
        "feedback": feedback,
        "timestamp": datetime.now(),
        "name": name,
        "registerNo": register_no,
        "class": student_class
    }

    result = collection.insert_one(document)

    if result.inserted_id:
        print(f"✅ Result stored in MongoDB with ID: {result.inserted_id}")
        return True
    else:
        print("❌ Failed to insert result into MongoDB.")
        return False
