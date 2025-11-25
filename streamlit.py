import streamlit as st
import requests

# Backend URL
BACKEND_URL = "http://localhost:8000"

st.set_page_config(page_title="Autonomous QA Agent", layout="wide")

st.title("🤖 Autonomous QA Agent")
st.write("A complete pipeline: Upload → Build KB → Generate Test Cases → Generate Selenium Scripts")

# --------------------------------------------------------------------
# TABS
# --------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📁 Build Knowledge Base", "🧪 Generate Test Cases", "🤖 Selenium Script Generator"])


# --------------------------------------------------------------------
# TAB 1 — Upload Files + Build KB
# --------------------------------------------------------------------
with tab1:
    st.header("📁 Step 1: Upload Files & Build Knowledge Base")

    html_file = st.file_uploader("Upload checkout.html", type=["html"])
    support_docs = st.file_uploader(
        "Upload support documents (MD, TXT, JSON, PDF, etc.)",
        type=["md", "txt", "json", "pdf"],
        accept_multiple_files=True
    )

    if st.button("Build Knowledge Base"):
        if html_file is None:
            st.error("⚠️ Please upload checkout.html")
        elif not support_docs:
            st.error("⚠️ Please upload at least one support document")
        else:
            with st.spinner("📚 Uploading and building knowledge base..."):
                files = {}

                # HTML file
                files["html_file"] = (html_file.name, html_file.read(), "text/html")

                # Support docs
                for i, doc in enumerate(support_docs):
                    files[f"support_docs"] = (
                        doc.name,
                        doc.read(),
                        "application/octet-stream"
                    )

                try:
                    response = requests.post(f"{BACKEND_URL}/upload_files", files=files)
                except Exception as e:
                    st.error("❌ Could not connect to backend. Is FastAPI running?")
                    st.stop()

            if response.status_code == 200:
                st.success("✅ Knowledge Base Built Successfully!")
                st.json(response.json())
            else:
                st.error("❌ Error building knowledge base")
                st.write(response.text)


# --------------------------------------------------------------------
# TAB 2 — Generate Test Cases
# --------------------------------------------------------------------
with tab2:
    st.header("🧪 Step 2: Generate Test Cases")

    user_query = st.text_input("Enter your test case request:", placeholder="e.g., Generate positive and negative test cases for discount code")

    if st.button("Generate Test Cases"):
        if not user_query.strip():
            st.error("⚠️ Please enter a query.")
        else:
            with st.spinner("⚙️ Generating test cases..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/generate_test_cases",
                        params={"query": user_query}
                    )
                except:
                    st.error("❌ Backend not reachable. Start FastAPI.")
                    st.stop()

            if response.status_code == 200:
                data = response.json()

                st.subheader("Raw LLM Output")
                st.code(data["raw_llm"], language="json")

                st.subheader("Parsed Test Cases")
                parsed = data["parsed"]
                if not parsed:
                    st.error("❌ No valid JSON extracted. LLM output was incomplete.")
                    st.stop()
                # FIX → st.json() only accepts dict, so wrap list
                if isinstance(parsed, list):
                    parsed = {"test_cases": parsed}

                st.json(parsed)
                st.session_state["parsed_test_cases"] = parsed

                st.subheader("Context Used")
                st.write(data["context_used"])
            else:
                st.error("❌ Error generating test cases")
                st.write(response.text)


# --------------------------------------------------------------------
# TAB 3 — Selenium Script Generator
# --------------------------------------------------------------------
with tab3:
    st.header("🤖 Step 3: Selenium Script Generator")

    # Ensure test cases exist
    if "parsed_test_cases" not in st.session_state:
        st.warning("⚠️ No test cases found. Generate them in Step 2 first.")
        st.stop()

    test_data = st.session_state["parsed_test_cases"]

    # Extract test case list
    test_cases = test_data["test_cases"]

    # Dropdown to select ID
    test_ids = [tc["id"] for tc in test_cases]
    selected_id = st.selectbox("Select Test Case ID", test_ids)

    # Fetch object
    selected_case = next(tc for tc in test_cases if tc["id"] == selected_id)

    st.subheader("Selected Test Case")
    st.json(selected_case)

    # Generate script
    if st.button("Generate Selenium Script"):
        with st.spinner("⚙️ Generating Selenium Script..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/generate_selenium_script",
                    json={"test_case": selected_case}
                )
                
                if response.status_code == 404:
                    st.error("❌ Endpoint not found.")
                    st.stop()
                elif response.status_code != 200:
                    st.error(f"❌ API Error: {response.status_code}")
                    st.write(response.text)
                    st.stop()
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to backend.")
                st.stop()
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")
                st.stop()

        result = response.json()

        # ✅ FIX: Check for "selenium_script" not "script"
        if not result.get("success", False):
            st.error("❌ Script generation failed")
            if result.get("errors"):
                for err in result["errors"]:
                    st.warning(f"⚠️ {err}")
            
            # Show what was returned for debugging
            if result.get("selenium_script"):
                st.subheader("Partial/Error Output:")
                st.code(result["selenium_script"], language="python")
            st.stop()

        # ✅ FIX: Use "selenium_script" field
        script_code = result.get("selenium_script", "")
        
        if not script_code:
            st.error("❌ No script generated")
            st.json(result)
            st.stop()

        st.success("✅ Script generated successfully!")
        st.subheader("Generated Selenium Script")
        st.code(script_code, language="python")
        
        # Download button
        st.download_button(
            label="📥 Download Script",
            data=script_code,
            file_name=f"{selected_case['id']}_selenium_test.py",
            mime="text/x-python"
        )
        
        # Show warnings if any
        if result.get("errors"):
            st.warning("⚠️ Notes:")
            for err in result["errors"]:
                st.write(f"- {err}")