import os
import google.generativeai as genai
from dotenv import load_dotenv

# ==============================
# 🌐 ENVIRONMENT SETUP
# ==============================

print("🔄 Loading environment variables...")
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found! Please check your .env file.")
else:
    print("✅ GEMINI_API_KEY loaded successfully!")

# ==============================
# 🔧 GEMINI CONFIGURATION
# ==============================

try:
    genai.configure(api_key=GEMINI_API_KEY)
    print("✅ Gemini API configured successfully!")
except Exception as e:
    print("❌ Error configuring Gemini API:", e)

# ==============================
# 🚀 LOAD GEMINI PRO MODEL
# ==============================

try:
    model = genai.GenerativeModel("gemini-1.5-pro")
    print("✅ Gemini Pro model loaded successfully!")
except Exception as e:
    print("❌ Error loading Gemini Pro model:", e)

# ==============================
# 📝 FUNCTION 1: Generate Feedback (Student Only)
# ==============================

def generate_feedback(student_text):
    print("\n🔎 Generating feedback for student submission...")
    try:
        prompt = f"""
        You are an experienced teacher grading a student's assignment.

        Analyze the following student submission and provide:
        1. Grade out of 10
        2. Strengths
        3. Areas for improvement
        4. Personalized feedback to help the student improve.

        Student Submission:
        {student_text}
        """

        print("📨 Sending prompt to Gemini API (Student Only)...")
        response = model.generate_content(prompt)
        print("✅ Received response from Gemini API!")

        return response.text

    except Exception as e:
        print("❌ Error from Gemini AI:", e)
        return f"❌ Error from Gemini AI: {str(e)}"

# ==============================
# 📝 FUNCTION 2: Compare Question Paper vs Answer Paper
# ==============================

def generate_feedback_comparison(question_text, answer_text):
    print("\n🔎 Generating feedback by comparing question paper and student answer...")
    try:
        prompt = f"""
        You are an expert examiner grading a student's answer based on a provided question paper or model answer.

        Compare the student's answer to the reference material and provide:
        1. Grade out of 10 based on accuracy, completeness, and relevance.
        2. Strengths in the student's answer.
        3. Areas where the student can improve.
        4. Personalized feedback explaining how the student can improve in future assignments.

        === Question Paper / Model Answer ===
        {question_text}

        === Student's Answer ===
        {answer_text}
        """

        print("📨 Sending comparison prompt to Gemini API...")
        response = model.generate_content(prompt)
        print("✅ Received response from Gemini API (Comparison)!")

        return response.text

    except Exception as e:
        print("❌ Error from Gemini AI during comparison:", e)
        return f"❌ Error from Gemini AI: {str(e)}"

# ==============================
# ✅ EXAMPLE TEST (Run this file directly)
# ==============================

if __name__ == "__main__":
    # Example student text
    student_text = "The process of photosynthesis involves converting sunlight into energy."

    # Call basic feedback function
    basic_feedback = generate_feedback(student_text)
    print("\n📋 BASIC FEEDBACK:\n", basic_feedback)

    # Example comparison
    #question_text = "Explain the process of photosynthesis in detail including the chemical reaction."
    #answer_text = "Photosynthesis converts sunlight into food in plants. Chlorophyll absorbs light energy."

    #comparison_feedback = generate_feedback_comparison(question_text, answer_text)
    #print("\n📋 COMPARISON FEEDBACK:\n", comparison_feedback)
