# Autonomous QA Agent for test case and script generation

A complete end-to-end system that generates **test cases** and **Selenium automation scripts** using a combination of:

* **FastAPI backend**
* **Streamlit UI**
* **RAG-based LLM test‑case generator**
* **FAISS vector database** for document retrieval
* **Dynamic Selenium script generator** using uploaded `checkout.html` structure

This README includes:

* Setup instructions
* How to run backend + frontend
* Usage flow
* Example requests
* Explanation of uploaded support documents

---

## 🚀 Features

* Upload project HTML + support documentation
* Build a local knowledge base using FAISS
* Automatically generate positive/negative test cases
* Use RAG to pull context from support docs
* Convert test cases into runnable Selenium Python scripts
* Download scripts directly from UI

---

# 📦 1. Installation & Setup

### ✔ Python Version

```
Python 3.10 or 3.11
```

### ✔ Create Virtual Environment

```
python -m venv .venv or uv venv (if using uv)
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate     # Windows
```

### ✔ Install Dependencies

Create `requirements.txt` (already included in repo):

```
fastapi
uvicorn
streamlit
requests
sentence-transformers
faiss-cpu
python-multipart
pydantic
beautifulsoup4
openai
```

Install:

```
pip install -r requirements.txt
```

---

# ⚙️ 2. Project Structure

```
project/
│── app.py                 # FastAPI Backend
│── streamlit.py           # Streamlit UI
│── backend/
│   ├── rag_agent.py
│   ├── vector_store.py
│   ├── script_generator.py
│   ├── processor.py
│   └── llm_test.py
│── data/
│   ├── html/              # Uploaded checkout.html
│   ├── uploads/           # Support docs
│   ├── vector_store.index # FAISS index
│── README.md
│── requirements.txt
```

---

# ▶️ 3. Running the Backend (FastAPI)

Start FastAPI server:

```
uvicorn app:app --reload
```

It runs at:

```
http://localhost:8000
```

### API Endpoints

| Method | Endpoint               | Description                                    |
| ------ | ---------------------- | ---------------------------------------------- |
| POST   | `/upload_files`        | Upload HTML + support docs & build FAISS index |
| POST   | `/generate_test_cases` | Generate RAG‑powered test cases                |
| POST   | `/generate_script`     | Convert selected test case → Selenium script   |
| GET    | `/health`              | Health check                                   |

---

# 🖥️ 4. Running the Frontend (Streamlit UI)

Start Streamlit:

```
streamlit run streamlit.py
```

Runs at:

```
http://localhost:8501
```

---

# 📘 5. Usage Flow (Step-by-Step)

## **Step 1 — Upload Files & Build KB**

You must upload:

* `checkout.html` (main HTML page)
* Support docs (md/txt/pdf/json)

Backend will:

* Parse docs
* Generate text dataset
* Build FAISS vector index

---

## **Step 2 — Generate Test Cases**

In Streamlit UI:

* Type query → “Generate test cases for email validation”
* Backend fetches relevant context using FAISS
* LLM produces structured JSON test cases

All test cases are stored in:

```
st.session_state["parsed_test_cases"]
```

---

## **Step 3 — Generate Selenium Script**

* Select a test case ID from dropdown
* Streamlit sends the test case to FastAPI
* Backend loads full HTML
* LLM generates Selenium script using actual selectors
* You can copy or download the script

---

# 🧪 6. Example Test Case Request

```
Generate 5 positive and negative test cases for checkout form validation.
Return strictly in JSON.
```

### Example Output

```
{
  "test_cases": [
    {
      "id": "TC001",
      "type": "positive",
      "steps": [...],
      "expected_output": "..."
    }
  ]
}
```

---

# 📄 7. Explanation of Support Documents

Support documents help the RAG engine understand your system.

### Recommended Types

| File Type | Purpose                                   |
| --------- | ----------------------------------------- |
| `.md`     | Functional requirements, specs, workflows |
| `.txt`    | Notes, validation rules, edge cases       |
| `.pdf`    | Business docs, user manuals               |
| `.json`   | API samples, UI structure, constraints    |

These files improve:

* Test‑case accuracy
* Form validation rules
* Data‑type constraints
* UI behavior understanding

---

# 🧠 8. How RAG Works Internally

1. Upload docs → merged into a text dataset
2. Chunk text + embed using Sentence Transformers
3. Store embeddings in FAISS
4. During test generation:

   * Query embedded
   * Top‑K context retrieved
   * Sent to LLM along with your prompt
5. LLM produces clean JSON test cases

---

# 🧩 9. Selenium Script Generation Logic

When a test case is selected:

1. Full HTML is loaded from `data/html/`
2. Test case is converted to text
3. Both are sent to LLM with a strict prompt
4. LLM returns ONLY Selenium Python code

The script uses:

* `WebDriverWait`
* Real CSS/XPath selectors from HTML
* Comments for each step

---

# 🏁 10. Future Enhancements

* Automatic selector validation
* Batch test-case generation
* End-to-end execution inside browser
* CI/CD integration
* Docker deployment

---

# 🤝 Contributing

Pull requests and improvements are welcome.

---

# 📄 License

MIT License
