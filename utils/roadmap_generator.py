import json
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import OllamaLLM

MODEL_NAME = 'qwen2.5-coder:1.5b'
MODEL_KEEP_ALIVE = '30m'  # keeps the model loaded between requests (no cold reloads)

def _is_valid_roadmap(data):
    """
    Checks the generated roadmap has a sensible hierarchy:
    at least 2 modules, every module has at least 2 topics,
    and every topic has at least 1 real learning point.
    """
    if not isinstance(data, dict) or 'modules' not in data:
        return False
    modules = data.get('modules', [])
    if not isinstance(modules, list) or len(modules) < 2:
        return False
    total_points = 0
    for module in modules:
        subtopics = module.get('subtopics', [])
        if len(subtopics) < 2:
            return False
        for sub in subtopics:
            points = sub.get('sub_subtopics', [])
            if not points:
                return False
            total_points += len(points)
    return total_points >= 10

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

def _build_chain(structure_rules, json_template):
    """LangChain pipeline: PromptTemplate | OllamaLLM | string parser."""
    # Make the JSON example literal text (LangChain treats {var} as a placeholder)
    json_literal = json_template.replace("{", "{{").replace("}", "}}")
    template = f"""
You are an expert curriculum designer and academic AI assistant.
Analyze the following syllabus text for the subject "{{subject}}" and break it down into a structured hierarchical learning roadmap.
{{feedback}}
{structure_rules}
{json_literal}
Remember: the final output tree should look like 3-5 modules -> 4-7 topics each -> 3-5 concrete sub-points each (roughly 40-60 learning points total).

Syllabus Text:
{{extracted_text}}
"""
    prompt = PromptTemplate(
        input_variables=["subject", "feedback", "extracted_text"],
        template=template,
    )
    llm = OllamaLLM(model=MODEL_NAME, temperature=0.3, keep_alive=MODEL_KEEP_ALIVE)
    return prompt | llm | StrOutputParser()

def generate_roadmap_from_text(subject_title, extracted_text):
    """
    Takes syllabus text and subject title, runs a LangChain pipeline over a
    local Ollama model, and returns a structured hierarchical JSON roadmap.
    Retries once with corrective feedback if the structure is too shallow.
    Raises RuntimeError when Ollama is unreachable or generation fails.
    """
    structure_rules = """
    STRICT STRUCTURAL RULES you must follow:
    1. The whole subject must be divided into 3 to 5 MAJOR modules (group related units together; NEVER one module per textbook unit).
    2. Each module must contain 4 to 7 topics inside it ("subtopics" in the JSON).
    3. Every topic must have 3 to 5 specific, concrete sub_topic details ("sub_subtopics" in the JSON).
    4. NEVER create a module with only 1 topic, and NEVER create a topic with fewer than 3 sub-subtopics.
    5. Sub-subtopics must be real learning points (definitions, operations, algorithms, properties) - NEVER just repeat the topic name or the module name as a sub-subtopic.
    6. EVERY field must be filled. Do not leave any list empty.
    """

    json_template = """
    Return ONLY a valid JSON object matching this exact structure, with no markdown formatting, no code block backticks, and no extra conversational text:
    {
        "subject": "Subject Name",
        "modules": [
            {
                "module_title": "Module Name (a broad area, e.g. Linear Data Structures)",
                "subtopics": [
                    {
                        "subtopic_title": "Topic Name (e.g. Arrays)",
                        "sub_subtopics": ["Specific detail 1 (e.g. Indexing and memory layout)", "Specific detail 2 (e.g. Insertion and deletion operations)", "Specific detail 3 (e.g. Applications of arrays)"]
                    },
                    {
                        "subtopic_title": "Another Topic (e.g. Stacks)",
                        "sub_subtopics": ["Push and pop operations", "Applications: overflow and underflow", "Stacks vs arrays"]
                    }
                ]
            }
        ]
    }
    """

    chain = _build_chain(structure_rules, json_template)

    def invoke_chain(feedback=""):
        raw_text = chain.invoke({
            "subject": subject_title,
            "feedback": feedback,
            # Smaller prompt = faster prompt evaluation on local models
            "extracted_text": extracted_text[:3000]
        })
        return _clean_json_output(raw_text)

    try:
        # First attempt
        roadmap_data = invoke_chain()

        # Output too shallow? Retry once with corrective feedback.
        if not _is_valid_roadmap(roadmap_data):
            print("Roadmap too shallow, retrying with stricter feedback...")
            feedback = (
                "YOUR PREVIOUS OUTPUT WAS REJECTED because it was too shallow: "
                "it had too few modules, modules with a single topic, or topics with no real sub-points. "
                "Regenerate the FULL roadmap strictly following the structural rules below. "
                "Split single-topic modules by grouping related topics, and expand sub-subtopics into concrete learning points."
            )
            retry_data = invoke_chain(feedback)
            if _is_valid_roadmap(retry_data):
                roadmap_data = retry_data

        return roadmap_data

    except Exception as e:
        print(f"Error generating local AI roadmap via Ollama: {e}")
        raise RuntimeError(
            "Ollama is not running or failed to generate a valid roadmap."
        ) from e
