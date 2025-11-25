import os
import json
import re
from typing import Dict, Any

from dotenv import load_dotenv
load_dotenv()

from backend.vector_store import search_vector_db

import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    raise RuntimeError("GEMINI_API_KEY not set in environment variables.")
model = genai.GenerativeModel("gemini-2.0-flash")


def call_llm(prompt: str, max_tokens: int = 2000) -> str:
    """
    Calls Gemini 2.5 Flash with the given prompt.
    Returns the raw text response.
    """
    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.4,
            "max_output_tokens": max_tokens,
            "response_mime_type": "application/json"
        }
    )

    try:
        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]

            if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                parts = candidate.content.parts
                collected = []

                for part in parts:
                    if hasattr(part, "text") and part.text:
                        collected.append(part.text)

                # If we got any text, return it
                if collected:
                    return "\n".join(collected)

        # If no parts received → return empty string instead of crashing
        return ""

    except Exception as e:
        # Never let Gemini crash your server
        return f""  # Safe fallback


# ---------------------------------------------------------
# 2. Extract JSON from LLM output safely
# ---------------------------------------------------------
def extract_first_json(text: str) -> Any:
    """Extract JSON from LLM output, handling markdown and nested structures."""
    text = text.strip()

    # Remove markdown code blocks
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find first { or [ and match to its closing brace
    # This handles nested structures properly
    start_char = None
    start_idx = None
    
    for i, char in enumerate(text):
        if char in '{[' and start_char is None:
            start_char = char
            start_idx = i
            break
    
    if start_idx is None:
        raise ValueError("No JSON object or array found in text")
    
    # Find matching closing brace
    closing = '}' if start_char == '{' else ']'
    depth = 0
    
    for i in range(start_idx, len(text)):
        if text[i] == start_char:
            depth += 1
        elif text[i] == closing:
            depth -= 1
            if depth == 0:
                # Found complete JSON
                candidate = text[start_idx:i+1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Found JSON structure but failed to parse: {e}")
    
    raise ValueError("No complete JSON found (unmatched braces)")


PROMPT_TEMPLATE = """
You are a Test Case Generator AI.  
Your job is ONLY to generate structured test cases based on the given context.  
This task is purely technical and does NOT involve harmful, unsafe, or personal content.

Always respond ONLY in valid JSON. No explanation, no markdown.

Your JSON must follow this structure exactly:

{{
  "test_cases": [
    {{
      "id": "TC001",
      "type": "positive or negative",
      "input": "input description",
      "steps": ["step 1", "step 2"],
      "expected_output": "expected system behavior"
    }}
  ]
}}

------------------------
CONTEXT:
{context}
------------------------

USER REQUEST:
{user_request}

IMPORTANT RULES:
- DO NOT add any explanation.
- DO NOT add text after the JSON.
- DO NOT truncate.
- Your entire reply MUST be a single complete JSON object.
- If response exceeds length, BREAK INTO FEWER TEST CASES instead of cutting JSON.
Generate all test cases now.
"""

def generate_test_cases(user_query: str, k: int = 6) -> Dict[str, Any]:
    """
    Full RAG pipeline:
    1. Retrieve relevant chunks from FAISS
    2. Send context + query to Gemini
    3. Parse JSON output
    """

    results = search_vector_db(user_query, top_k=k)

    if not isinstance(results, list) or not results or not isinstance(results[0], tuple):
        return {
            "error": "Vector DB not ready. Please upload files and build knowledge base.",
            "raw_llm": None,
            "parsed": None,
            "used_context": []
        }

    # Build context text
    context_blocks = []
    for i, (chunk_text, dist) in enumerate(results):
        snippet = chunk_text.strip()
        if len(snippet) > 800:
            snippet = snippet[:800] + " ...[truncated]..."
        context_blocks.append(f"[CHUNK {i+1} | distance={dist}]\n{snippet}")

    context = "\n\n".join(context_blocks)

   
    prompt = PROMPT_TEMPLATE.format(context=context, user_request=user_query)

   
    raw_response = call_llm(prompt, max_tokens=1200)

   
    parsed = None
    error = None
    try:
        parsed = extract_first_json(raw_response)
    except Exception as e:
        error = f"JSON parsing failed: {e}"

    return {
        "raw_llm": raw_response,
        "parsed": parsed,
        "error": error,
        "used_context": context_blocks
    }

