from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import re
from werkzeug.utils import secure_filename

# Importing your custom service functions
from services.pdf_service import process_pdf_with_structured_output

from services.ai_service import generate_feedback
from services.db_service import store_result, collection  # Import the MongoDB collection for queries
from services.ai_service import generate_feedback_comparison

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB limit

# Ensure uploads folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ------------------------
# Utility Functions
# ------------------------

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_grade(feedback):
    match = re.search(r'Grade[:]*\s*(\d{1,2}\/10)', feedback, re.IGNORECASE)
    if match:
        grade = match.group(1)
        print(f"✅ Extracted grade: {grade}")
        return grade
    else:
        print("⚠️ No grade found in feedback. Defaulting to 'N/A'.")
        return "N/A"

# ------------------------
# Routes
# ------------------------

@app.route('/')
def index():
    return render_template('teacher1.html')

# Analyze and Grade Route (Only analyzes, doesn't store)
@app.route('/teacher/analyze_and_grade', methods=['POST'])
def analyze_and_grade():
    if "file" not in request.files:
        return jsonify({"message": "❌ No file uploaded"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"message": "❌ No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"message": "❌ Only PDF files are allowed"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    try:
        print("📝 Starting text extraction...")
        extracted_text = process_pdf_with_structured_output(filepath)
    except Exception as e:
        return jsonify({"message": f"❌ Error extracting text: {e}"}), 500

    if not extracted_text:
        return jsonify({"message": "❌ No text found in the PDF"}), 400

    try:
        print("🤖 Sending text to AI for feedback...")
        feedback = generate_feedback(extracted_text)
    except Exception as e:
        return jsonify({"message": f"❌ Error generating feedback: {e}"}), 500

    try:
        os.remove(filepath)
    except Exception as e:
        print(f"⚠️ Warning: Could not delete file {filepath}: {e}")

    grade = extract_grade(feedback)

    # Return feedback & grade but do not store yet!
    return jsonify({
        "message": "✅ Grading complete!",
        "grade": grade,
        "feedback": feedback
    }), 200

# Store Feedback Route (Teacher decides when to store)
@app.route('/teacher/store_feedback', methods=['POST'])
def store_feedback():
    data = request.get_json()

    filename = data.get("filename")
    grade = data.get("grade")
    feedback = data.get("feedback")
    name = data.get("name")
    register_no = data.get("register_no")
    student_class = data.get("student_class")

    if not filename or not grade or not feedback or not name or not register_no or not student_class:
        return jsonify({"message": "❌ Missing required fields!"}), 400

    try:
        store_result(filename, grade, feedback, name, register_no, student_class)
        return jsonify({"message": "✅ Feedback and grade stored successfully!"}), 200
    except Exception as e:
        print(f"❌ Error storing feedback: {e}")
        return jsonify({"message": f"❌ Error storing feedback: {e}"}), 500
    

# Student View Result Route
@app.route('/student/view_result', methods=['POST'])
def student_view_result():
    data = request.get_json()

    name = data.get("name")
    register_no = data.get("register_no")
    student_class = data.get("student_class")

    if not name or not register_no or not student_class:
        return jsonify({"message": "❌ Missing required fields!"}), 400

    try:
        # Query MongoDB for the student result
        query = {
            "name": name,
            "registerNo": register_no,
            "class": student_class
        }

        print(f"🔎 Searching for student record: {query}")

        result = collection.find_one(query)

        if result:
            return jsonify({
                "grade": result.get("grade", "N/A"),
                "feedback": result.get("feedback", "No feedback found")
            }), 200
        else:
            return jsonify({"message": "❌ No result found for the given credentials."}), 404

    except Exception as e:
        print(f"❌ Error retrieving student result: {e}")
        return jsonify({"message": f"❌ Error retrieving student result: {e}"}), 500

# ------------------------
# Run Server
# ------------------------
@app.route('/teacher/compare_and_grade', methods=['POST'])
def compare_and_grade():
    if 'questionPaper' not in request.files or 'answerPaper' not in request.files:
        return jsonify({"message": "❌ Both files are required!"}), 400

    question_file = request.files['questionPaper']
    answer_file = request.files['answerPaper']

    if not allowed_file(question_file.filename) or not allowed_file(answer_file.filename):
        return jsonify({"message": "❌ Invalid file format! Only PDF files allowed."}), 400

    q_filename = secure_filename(question_file.filename)
    a_filename = secure_filename(answer_file.filename)

    q_filepath = os.path.join(app.config["UPLOAD_FOLDER"], q_filename)
    a_filepath = os.path.join(app.config["UPLOAD_FOLDER"], a_filename)

    question_file.save(q_filepath)
    answer_file.save(a_filepath)

    try:
        print("📝 Extracting question paper text...")
        question_text = process_pdf_with_structured_output(q_filepath)
        print(f"✅ Question text extracted ({len(question_text)} chars)")

        print("📝 Extracting answer paper text...")
        answer_text = process_pdf_with_structured_output(a_filepath)
        print(f"✅ Answer text extracted ({len(answer_text)} chars)")

        if not question_text or not answer_text:
            return jsonify({"message": "❌ Failed to extract text from one or both PDFs!"}), 400

    except Exception as e:
        return jsonify({"message": f"❌ Error extracting PDF text: {e}"}), 500

    try:
        feedback = generate_feedback_comparison(question_text, answer_text)
    except Exception as e:
        return jsonify({"message": f"❌ Error generating feedback: {e}"}), 500

    grade = extract_grade(feedback)

    try:
        os.remove(q_filepath)
        os.remove(a_filepath)
    except Exception as e:
        print(f"⚠️ Could not delete temp files: {e}")

    return jsonify({
        "message": "✅ Grading complete!",
        "grade": grade,
        "feedback": feedback
    }), 200



if __name__ == "__main__":
    print("🚀 Server running at http://127.0.0.1:5001/")
    app.run(debug=True, port=5001)
