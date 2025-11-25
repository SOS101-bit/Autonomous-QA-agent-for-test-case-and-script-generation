from fastapi import FastAPI, UploadFile, File, Query
import os
from backend.processor import build_processed_dataset
from backend.vector_store import build_faiss_index
from backend.rag_agent import generate_test_cases
from backend.script_generator import generate_selenium_script
from backend.llm_test import test_llm
from pydantic import BaseModel
import json

app = FastAPI()

UPLOAD_DIR = "data/uploads/"
HTML_DIR = "data/html/"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(HTML_DIR, exist_ok=True)

@app.get("/")
def home():
    return {'message':'Autonomous QA Agent for test script generation'}

@app.get('/health')
def health_check():
    return{
        'status':'OK'
    }

@app.get('/test_llm')
def test_llm_api():
    out = test_llm("Say 'LLM working' in one line.")
    return {"output": out}

@app.post("/upload_files")
async def upload_files(html_file: UploadFile = File(...), support_docs: list[UploadFile] = File(...)):
    
    # Save HTML file
    html_path = os.path.join(HTML_DIR, html_file.filename)
    with open(html_path, "wb") as f:
        f.write(await html_file.read())

    # Save support documents
    for doc in support_docs:
        doc_path = os.path.join(UPLOAD_DIR, doc.filename)
        with open(doc_path, "wb") as f:
            f.write(await doc.read())

    processed_text = build_processed_dataset()
    faiss_info = build_faiss_index(processed_text)

    return{
        'message': "Files uploaded and processed successfully",
        'processed length': len(processed_text),
        'faiss info': faiss_info["num_chunks"]
    }

@app.post("/generate_test_cases")
def generate_test_cases_api(query: str = Query(..., description="User query for test case generation")):
    """
    API endpoint to run the RAG test case generator.
    Example query:
    {
        "query": "Generate checkout page test cases"
    }
    """
    result = generate_test_cases(query)

    if result["parsed"] is None:
        return {
            "query": query,
            "raw_llm": result["raw_llm"],
            "parsed": None,
            "error": "LLM output too large or incomplete. Try requesting fewer test cases.",
            "context_used": result["used_context"]
        }

    return {
        "query": query,
        "raw_llm": result["raw_llm"],
        "parsed": result["parsed"],
        "error": result["error"],
        "context_used": result["used_context"]
    }

class SeleniumRequest(BaseModel):
    test_case: dict

@app.post("/generate_selenium_script")
def generate_selenium_api(test_case: dict):
    """Generate Selenium script for a test case."""
    
    script, errors = generate_selenium_script(test_case)
    
    return {
        "test_case_id": test_case.get("id"),
        "selenium_script": script,
        "errors": errors,
        "success": len(errors) == 0
    }