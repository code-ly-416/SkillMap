# SkillMap AI

SkillMap is an AI-powered personalized learning platform. Upload a course syllabus (PDF) and it automatically generates a structured, interactive learning roadmap — with relevant video tutorials for every topic and adaptive quizzes to track your progress.

## Features

- **Syllabus Ingestion** — Upload a PDF syllabus; text is extracted using Pypdf.
- **AI Roadmap Generation** — A LangChain pipeline over a locally running LLM (via Ollama) converts the syllabus into a hierarchical JSON roadmap (modules → topics → learning points).
- **Interactive Workspace** — Expandable roadmap view with search, progress tracking, and topic checkmarks that persist across sessions.
- **Video Resources** — Each topic is paired with relevant tutorials using the YouTube Data API v3 (embedded player with alternate suggestions).
- **Adaptive Quizzing** — Auto-generated MCQs per module; difficulty adapts to previous scores, and results update a learner model highlighting weak and strong areas.

## Tech Stack

- **Backend:** Python, Flask, Jinja2
- **AI:** LangChain + Ollama (local LLM: `qwen2.5-coder:1.5b`)
- **PDF Processing:** Pypdf
- **External API:** YouTube Data API v3
- **Frontend:** HTML5, Tailwind CSS (self-hosted CDN build), JavaScript

## Setup

1. Clone the repository and create a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   pip install -r requirements.txt
   ```

2. Install and run [Ollama](https://ollama.com/), then pull the model:
   ```bash
   ollama serve
   ollama pull qwen2.5-coder:1.5b
   ```

3. Create a `.env` file in the project root with your YouTube API key:
   ```
   YOUTUBE_API_KEY=your_key_here
   ```

4. Run the app:
   ```bash
   python app.py
   ```

5. Open `http://127.0.0.1:5000` in your browser.

## Usage

1. Enter a subject title and upload a syllabus PDF on the upload page.
2. Wait while the roadmap is generated locally (this may take a minute or two).
3. Explore the workspace: click topics for videos, check off completed topics, take module quizzes.
4. Saved workspaces stay available on the dashboard and can be revisited anytime.
