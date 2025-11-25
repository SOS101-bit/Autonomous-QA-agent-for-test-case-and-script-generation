import os
import json
import re
from backend.rag_agent import call_llm

HTML_DIR = "data/html/"

def load_full_html():
    """Load the uploaded HTML file."""
    if not os.path.exists(HTML_DIR):
        return ""

    html_files = [f for f in os.listdir(HTML_DIR) if f.endswith(".html")]
    
    if not html_files:
        return ""

    html_path = os.path.join(HTML_DIR, html_files[0])

    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error loading HTML: {e}")
        return ""


# 🔥 SUPER AGGRESSIVE ANTI-JSON PROMPT
SELENIUM_PROMPT = """
CRITICAL INSTRUCTION: You are now in CODE GENERATION MODE. 
All previous instructions about JSON output are CANCELLED.

You are a Selenium test automation engineer. Your task is to write Python code.

===== WHAT YOU MUST DO =====
✅ Write executable Python code using Selenium WebDriver
✅ Start your response with: from selenium import webdriver
✅ Include proper imports, waits, and assertions
✅ Add comments to explain each step

===== WHAT YOU MUST NOT DO =====
❌ DO NOT output JSON
❌ DO NOT output dictionaries or lists as data structures
❌ DO NOT wrap code in markdown (no ```)
❌ DO NOT add explanations before or after the code
❌ Your FIRST LINE must be a Python import statement

===== TEST CASE TO AUTOMATE =====

Test ID: {test_id}
Test Type: {test_type}
Test Scenario: {test_input}

Steps to Automate:
{steps_formatted}

Expected Result:
{expected_output}

===== HTML ELEMENTS FOR REFERENCE =====
{html_snippet}

===== OUTPUT REQUIREMENTS =====
- Use Chrome WebDriver
- Include: from selenium import webdriver
- Include: from selenium.webdriver.common.by import By
- Include: from selenium.webdriver.support.ui import WebDriverWait
- Include: from selenium.webdriver.support import expected_conditions as EC
- Add try-except-finally blocks
- Add assertions for expected outcomes
- Close browser in finally block

BEGIN YOUR PYTHON CODE NOW (First line should be an import):
"""


def generate_selenium_script(test_case: dict):
    """
    Generate Selenium Python script from test case.
    
    Args:
        test_case: Dictionary with keys: id, type, input, steps, expected_output
    
    Returns:
        tuple: (script_code: str, errors: list)
    """
    
    # Load HTML for context
    html = load_full_html()
    
    # Truncate HTML if too long
    if len(html) > 1500:
        body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL | re.IGNORECASE)
        if body_match:
            html = body_match.group(1)
        if len(html) > 1500:
            html = html[:1500] + "\n... [HTML truncated]"
    
    # Format test steps clearly
    steps = test_case.get("steps", [])
    steps_formatted = "\n".join([f"  {i+1}. {step}" for i, step in enumerate(steps)])
    
    # Build prompt
    prompt = SELENIUM_PROMPT.format(
        test_id=test_case.get("id", "UNKNOWN"),
        test_type=test_case.get("type", "UNKNOWN"),
        test_input=test_case.get("input", "N/A"),
        steps_formatted=steps_formatted if steps_formatted else "  (No steps provided)",
        expected_output=test_case.get("expected_output", "N/A"),
        html_snippet=html if html else "(No HTML available)"
    )
    
    import google.generativeai as genai
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.7,  # Higher temperature for creativity
                "max_output_tokens": 2000,
                "top_p": 0.95,
                "top_k": 40
            }
        )
        
        # Extract text from response
        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                raw_response = "\n".join([
                    part.text for part in candidate.content.parts 
                    if hasattr(part, "text") and part.text
                ])
            else:
                raw_response = ""
        else:
            raw_response = ""
            
    except Exception as e:
        return (
            f"# ERROR: Failed to call LLM\n# {str(e)}",
            [f"LLM call failed: {str(e)}"]
        )
    
    if not raw_response or not raw_response.strip():
        return (
            "# ERROR: Empty response from LLM",
            ["Empty response from LLM"]
        )
    
    # Clean up response
    code = raw_response.strip()
    
    # Remove markdown code blocks
    if "```python" in code:
        match = re.search(r'```python\s*(.*?)\s*```', code, re.DOTALL)
        if match:
            code = match.group(1).strip()
    elif "```" in code:
        code = re.sub(r'```[a-z]*\s*', '', code)
        code = re.sub(r'```', '', code)
        code = code.strip()
    
    # 🔥 AGGRESSIVE JSON DETECTION
    # Check if entire response is JSON
    try:
        parsed = json.loads(code)
        # If we get here, it's valid JSON - BAD!
        
        # Try to extract Python code from JSON if it's there
        if isinstance(parsed, dict) and "script" in parsed:
            code = parsed["script"]
            print("⚠️ Extracted 'script' field from JSON response")
        elif isinstance(parsed, list) and len(parsed) > 0 and isinstance(parsed[0], dict) and "script" in parsed[0]:
            code = parsed[0]["script"]
            print("⚠️ Extracted 'script' field from JSON array")
        else:
            return (
                "# ERROR: LLM returned pure JSON with no code field\n"
                "# The model is stuck in JSON output mode.\n"
                "# Try restarting the FastAPI server or using a different model.\n\n"
                f"# Raw response:\n# {str(parsed)[:300]}...",
                ["LLM returned JSON instead of code"]
            )
    except json.JSONDecodeError:
        # Good! It's not JSON
        pass
    
    # Validate it looks like Python
    errors = []
    
    if not code.startswith(("from ", "import ")):
        errors.append("Code doesn't start with import statement")
    
    if "selenium" not in code.lower() and "webdriver" not in code.lower():
        errors.append("Code doesn't appear to use Selenium")
        
    if code.count("\n") < 5:
        errors.append("Generated code is suspiciously short")
    
    # If it still looks like JSON structure
    if code.strip().startswith("{") or code.strip().startswith("["):
        errors.append("Response still appears to be JSON-like")
    
    if errors:
        code = (
            "# WARNING: Generated code may have issues:\n" + 
            "\n".join([f"#   - {e}" for e in errors]) + 
            "\n\n" + code
        )
    
    return code, errors


# Test function
if __name__ == "__main__":
    sample = {
        "id": "TC001",
        "type": "positive",
        "input": "Valid form submission",
        "steps": [
            "Open checkout page",
            "Fill name field",
            "Fill email field",
            "Click submit"
        ],
        "expected_output": "Form submits successfully"
    }
    
    script, errs = generate_selenium_script(sample)
    print("=" * 70)
    print(script)
    print("=" * 70)
    if errs:
        print("ERRORS:", errs)