from flask import Flask, render_template, request
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from utils.pdf_parser import extract_text_from_pdf

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
        
        # Extract text using our parser utility
        extracted_text = extract_text_from_pdf(filepath)
        
        # Display preview of extracted text
        return f"""
        <h1>Syllabus Processed Successfully!</h1>
        <p><strong>Subject:</strong> {subject}</p>
        <p><strong>Extracted Character Count:</strong> {len(extracted_text)} characters</p>
        <hr>
        <h3>Extracted Text Preview:</h3>
        <p>{extracted_text[:1000]}...</p>
        <br><a href="/">← Back to Home</a>
        """
    
    return "Invalid file type. Only PDF allowed.", 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
