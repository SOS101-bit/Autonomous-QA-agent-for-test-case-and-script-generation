import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY missing from .env")

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")

def test_llm(prompt: str):
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0,
                "max_output_tokens": 200
            }
        )

        if response.candidates:
            parts = response.candidates[0].content.parts
            out = "".join([p.text for p in parts if hasattr(p, "text") and p.text])
            return out

        return ""

    except Exception as e:
        return f"ERROR: {str(e)}"
