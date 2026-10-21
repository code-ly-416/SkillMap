import json
import ollama

def generate_roadmap_from_text(subject_title, extracted_text):
    """
    Takes syllabus text and subject title, sends it to local Ollama instance,
    and returns a structured hierarchical JSON roadmap.
    """
    prompt = f"""
    You are an expert curriculum designer and academic AI assistant. 
    Analyze the following syllabus text for the subject "{subject_title}" and break it down into a structured hierarchical learning roadmap.
    
    Return ONLY a valid JSON object matching this exact structure, with no markdown formatting, no code block backticks, and no extra conversational text:
    {{
        "subject": "{subject_title}",
        "modules": [
            {{
                "module_title": "Module Name",
                "subtopics": [
                    {{
                        "subtopic_title": "Subtopic Name",
                        "sub_subtopics": ["Detail 1", "Detail 2"]
                    }}
                ]
            }}
        ]
    }}

    Syllabus Text:
    {extracted_text[:4000]}
    """

    try:
        # Calls local Ollama running on your machine (default port 11434)
        # Change model name here if you use 'qwen2.5-coder:1.5b' or 'llama3'
        response = ollama.generate(
            model='qwen2.5-coder:1.5b',
            prompt=prompt,
            options={'temperature': 0.2}
        )
        
        raw_text = response['response'].strip()
        
        # Clean potential markdown block formatting from local model output
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
            
        roadmap_data = json.loads(raw_text.strip())
        return roadmap_data
        
    except Exception as e:
        print(f"Error generating local AI roadmap via Ollama: {e}")
        # Fallback structure if Ollama is not running or fails
        return {
            "subject": subject_title,
            "modules": [
                {
                    "module_title": "Error Processing Syllabus Locally",
                    "subtopics": [
                        {"subtopic_title": "Ensure Ollama is running (`ollama serve`)", "sub_subtopics": [str(e)]}
                    ]
                }
            ]
        }
