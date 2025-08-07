import os
from flask import Flask, render_template, request, redirect, url_for, flash
from PIL import Image
import pytesseract
import openai
from dotenv import load_dotenv
import tempfile

# Load env vars
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set tesseract path (adjust if needed)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Needed for flashing messages

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_image(path):
    try:
        image = Image.open(path)
        return pytesseract.image_to_string(image)
    except Exception as e:
        return f"Error during OCR: {str(e)}"

def call_openai(text, doc_type):
    if doc_type == "resume":
        prompt = f"""
You are an AI assistant. Extract:
- Full Name
- Email
- Phone Number
- Education
- Skills
- Work Experience

Text:
{text}

Return as JSON.
"""
    elif doc_type == "aadhaar":
        prompt = f"""
Extract from Aadhaar:
- Full Name
- Aadhaar Number
- DOB/YOB
- Gender

Text:
{text}

Return as JSON.
"""
    elif doc_type == "note":
        prompt = f"""
Summarize the handwritten note into key bullet points.

Text:
{text}

Return the summary only.
"""
    else:
        return "Unsupported document type."

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"OpenAI Error: {str(e)}"

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    ocr_text = None
    if request.method == "POST":
        doc_type = request.form.get("doc_type")
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # Save file temporarily
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                file.save(tmp.name)
                ocr_text = extract_text_from_image(tmp.name)
                result = call_openai(ocr_text, doc_type)
            os.unlink(tmp.name)  # remove temp file
        else:
            flash("File type not allowed")

    return render_template("index.html", result=result, ocr_text=ocr_text)

if __name__ == "__main__":
    app.run(debug=True)
