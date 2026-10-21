from flask import Flask, render_template, request, redirect, url_for, abort
import os
import json
import uuid
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from utils.pdf_parser import extract_text_from_pdf
from utils.roadmap_generator import generate_roadmap_from_text

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['WORKSPACE_FOLDER'] = 'workspaces'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['WORKSPACE_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def home():
    return render_template('upload.html')

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
        roadmap_json['source_file'] = filename

        # 3. Save workspace so it can be revisited
        roadmap_id = uuid.uuid4().hex[:8]
        workspace_path = os.path.join(app.config['WORKSPACE_FOLDER'], f"{roadmap_id}.json")
        with open(workspace_path, 'w', encoding='utf-8') as f:
            json.dump(roadmap_json, f, indent=2, ensure_ascii=False)

        return redirect(url_for('workspace', roadmap_id=roadmap_id))

    return "Invalid file type. Only PDF allowed.", 400

@app.route('/workspace/<roadmap_id>')
def workspace(roadmap_id):
    # Only allow safe ids we generated ourselves (8 hex chars)
    if len(roadmap_id) != 8 or not all(c in '0123456789abcdef' for c in roadmap_id):
        abort(404)

    workspace_path = os.path.join(app.config['WORKSPACE_FOLDER'], f"{roadmap_id}.json")
    if not os.path.exists(workspace_path):
        abort(404)

    with open(workspace_path, 'r', encoding='utf-8') as f:
        roadmap = json.load(f)

    topic_count = sum(len(m.get('subtopics', [])) for m in roadmap.get('modules', []))

    return render_template(
        'workspace.html',
        roadmap=roadmap,
        topic_count=topic_count
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)
