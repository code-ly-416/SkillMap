from flask import Flask, render_template, request, redirect, url_for, abort, jsonify
import os
import json
import uuid
import datetime
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from utils.pdf_parser import extract_text_from_pdf
from utils.youtube_api import search_videos
from utils.roadmap_generator import generate_roadmap_from_text
from utils.quiz_generator import generate_quiz

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['WORKSPACE_FOLDER'] = 'workspaces'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['WORKSPACE_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def _load_roadmap(roadmap_id):
    """Loads a workspace roadmap JSON, or None if the id/workspace is invalid."""
    if len(roadmap_id) != 8 or not all(c in '0123456789abcdef' for c in roadmap_id):
        return None
    workspace_path = os.path.join(app.config['WORKSPACE_FOLDER'], f"{roadmap_id}.json")
    if not os.path.exists(workspace_path):
        return None
    with open(workspace_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def _progress_path(roadmap_id):
    return os.path.join(app.config['WORKSPACE_FOLDER'], f"{roadmap_id}.progress.json")

def _load_progress(roadmap_id):
    """Learner model: quiz results per module + correct/wrong counts per topic."""
    path = _progress_path(roadmap_id)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"quiz_results": {}, "topic_stats": {}}

def _save_progress(roadmap_id, progress):
    with open(_progress_path(roadmap_id), 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)

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
    roadmap = _load_roadmap(roadmap_id)
    if roadmap is None:
        abort(404)

    topic_count = sum(len(m.get('subtopics', [])) for m in roadmap.get('modules', []))

    # Learner model summary: best/last quiz score per module for the UI badges
    progress = _load_progress(roadmap_id)
    quiz_scores = {}
    for module_index, results in progress.get('quiz_results', {}).items():
        if results:
            last = results[-1]
            quiz_scores[str(module_index)] = f"{last['score']}/{last['total']}"

    return render_template(
        'workspace.html',
        roadmap=roadmap,
        roadmap_id=roadmap_id,
        topic_count=topic_count,
        quiz_scores=quiz_scores
    )

@app.route('/api/videos')
def api_videos():
    topic = request.args.get('topic', '').strip()
    if not topic:
        return jsonify([])

    videos = search_videos(topic, max_results=3)
    return jsonify(videos)

@app.route('/api/quiz/<roadmap_id>', methods=['POST'])
def api_quiz(roadmap_id):
    roadmap = _load_roadmap(roadmap_id)
    if roadmap is None:
        return jsonify({"error": "Workspace not found."}), 404

    data = request.get_json(silent=True) or {}
    module_index = data.get('module_index')
    modules = roadmap.get('modules', [])
    if not isinstance(module_index, int) or module_index < 0 or module_index >= len(modules):
        return jsonify({"error": "Invalid module."}), 400

    module = modules[module_index]

    # Serve cached quiz for this module if we already generated one
    quizzes_path = os.path.join(app.config['WORKSPACE_FOLDER'], f"{roadmap_id}.quizzes.json")
    quizzes = {}
    if os.path.exists(quizzes_path):
        with open(quizzes_path, 'r', encoding='utf-8') as f:
            quizzes = json.load(f)
    if str(module_index) in quizzes:
        return jsonify(quizzes[str(module_index)])

    # Adapt difficulty to the learner's current proficiency
    progress = _load_progress(roadmap_id)
    results = progress.get('quiz_results', {}).get(str(module_index), [])
    if results:
        last = results[-1]
        proficiency = (
            f"retry (learner scored {last['score']}/{last['total']} previously - "
            f"ask harder, more applied questions)"
        )
    else:
        proficiency = "first attempt (ask fundamental questions)"

    subtopic_titles = [s['subtopic_title'] for s in module.get('subtopics', [])]
    quiz = generate_quiz(roadmap.get('subject', ''), module['module_title'], subtopic_titles, proficiency)

    if quiz is None:
        return jsonify({"error": "Could not generate the quiz. Make sure Ollama is running."}), 503

    # Cache so revisiting this module reuses the same quiz
    quizzes[str(module_index)] = quiz
    with open(quizzes_path, 'w', encoding='utf-8') as f:
        json.dump(quizzes, f, indent=2, ensure_ascii=False)

    return jsonify(quiz)

@app.route('/api/quiz/<roadmap_id>/submit', methods=['POST'])
def api_quiz_submit(roadmap_id):
    if _load_roadmap(roadmap_id) is None:
        return jsonify({"error": "Workspace not found."}), 404

    data = request.get_json(silent=True) or {}
    module_index = str(data.get('module_index'))
    answers = data.get('answers', [])

    quizzes_path = os.path.join(app.config['WORKSPACE_FOLDER'], f"{roadmap_id}.quizzes.json")
    if not os.path.exists(quizzes_path):
        return jsonify({"error": "No generated quiz found for this workspace."}), 400
    with open(quizzes_path, 'r', encoding='utf-8') as f:
        quizzes = json.load(f)
    quiz = quizzes.get(module_index)
    if quiz is None:
        return jsonify({"error": "No generated quiz found for this module."}), 400

    questions = quiz['questions']
    progress = _load_progress(roadmap_id)
    topic_stats = progress.setdefault('topic_stats', {})
    quiz_results = progress.setdefault('quiz_results', {})

    results = []
    score = 0
    weak_topics = []
    strong_topics = []

    for i, q in enumerate(questions):
        chosen = answers[i] if i < len(answers) else None
        correct = isinstance(chosen, int) and 0 <= chosen < len(q['options']) and chosen == q['answer']
        if correct:
            score += 1

        topic = q.get('topic') or q['question'][:50]
        stats = topic_stats.setdefault(topic, {"correct": 0, "wrong": 0})
        if correct:
            stats['correct'] += 1
            if topic not in strong_topics:
                strong_topics.append(topic)
        else:
            stats['wrong'] += 1
            if topic not in weak_topics:
                weak_topics.append(topic)

        chosen_text = q['options'][chosen] if isinstance(chosen, int) and 0 <= chosen < len(q['options']) else None
        results.append({
            "question": q['question'],
            "chosen": chosen_text,
            "correct": correct,
            "correct_answer": q['options'][q['answer']],
            "explanation": q.get('explanation', '')
        })

    quiz_results.setdefault(module_index, []).append({
        "score": score,
        "total": len(questions),
        "date": datetime.datetime.now().isoformat(timespec='seconds')
    })
    _save_progress(roadmap_id, progress)

    return jsonify({
        "score": score,
        "total": len(questions),
        "results": results,
        "weak_topics": weak_topics,
        "strong_topics": strong_topics
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
