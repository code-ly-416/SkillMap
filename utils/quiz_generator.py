import json
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import OllamaLLM

MODEL_NAME = 'qwen2.5-coder:1.5b'
MODEL_KEEP_ALIVE = '30m'  # keeps the model loaded between requests (no cold reloads)

def _clean_json_output(raw_text):
    raw_text = raw_text.strip()
    # Clean potential markdown block formatting from local model output
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    if raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
    return json.loads(raw_text.strip())

def generate_quiz(subject_title, module_title, subtopics, proficiency="first attempt"):
    """
    Generates a short MCQ quiz for one roadmap module using a LangChain
    pipeline over a local Ollama model.
    Proficiency adapts difficulty: 'first attempt' -> fundamental questions,
    'retry (previous score x/y)' -> more advanced/applied questions.
    Returns dict with module_title + questions list, or None on failure.
    """
    topic_list = "\n".join("- " + t for t in subtopics)

    json_example = """
    {
        "questions": [
            {
                "topic": "the exact subtopic from the list above that this question tests",
                "question": "question text",
                "options": ["option A", "option B", "option C", "option D"],
                "answer": 0,
                "explanation": "one sentence explaining why the answer is correct"
            }
        ]
    }
    """
    json_literal = json_example.replace("{", "{{").replace("}", "}}")

    template = f"""
You are an expert exam writer for the subject "{{subject}}".

Write a quiz for the module "{{module_title}}" covering these topics:
{{topics}}

Learner proficiency: {{proficiency}}
- If this is a first attempt, ask fundamental questions.
- If the learner is retrying after a previous attempt, ask more advanced and applied questions.

Return ONLY a valid JSON object, no markdown formatting, no code block backticks, no extra text:
{json_literal}

Rules:
- Exactly 5 questions.
- Each question has exactly 4 options.
- "answer" is the 0-based index of the correct option.
- Each question must test a different topic from the list.
"""

    prompt = PromptTemplate(
        input_variables=["subject", "module_title", "topics", "proficiency"],
        template=template,
    )
    llm = OllamaLLM(model=MODEL_NAME, temperature=0.4, keep_alive=MODEL_KEEP_ALIVE)
    chain = prompt | llm | StrOutputParser()

    try:
        data = _clean_json_output(chain.invoke({
            "subject": subject_title,
            "module_title": module_title,
            "topics": topic_list,
            "proficiency": proficiency,
        }))

        questions = data.get('questions', [])
        valid = [
            q for q in questions
            if isinstance(q.get('question'), str)
            and isinstance(q.get('options'), list) and len(q['options']) == 4
            and isinstance(q.get('answer'), int) and 0 <= q['answer'] <= 3
        ]
        if valid:
            return {"module_title": module_title, "questions": valid[:5]}

    except Exception as e:
        print(f"Error generating quiz via Ollama: {e}")

    return None
