from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from utils.pdf_parser import extract_text_from_pdf
from utils.roadmap_generator import generate_roadmap_from_text

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'syllabus' not in request.files:
        return "No file part", 400
    
    file = request.files['syllabus']
    subject = request.form.get('subject', 'General Subject')
    
    if file.filename == '':
        return "No selected file", 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 1. Extract text from PDF
        extracted_text = extract_text_from_pdf(filepath)
        
        # 2. Generate AI Roadmap
        roadmap_json = generate_roadmap_from_text(subject, extracted_text)
        
        # For now, return JSON preview to verify it works
        return jsonify(roadmap_json)
    
    return "Invalid file type. Only PDF allowed.", 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
