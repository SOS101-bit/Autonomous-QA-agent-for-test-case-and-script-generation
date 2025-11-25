import os
from bs4 import BeautifulSoup
import PyPDF2

def extract_text_from_html(html_path: str) -> str:
    
    with open(html_path, "r",encoding="utf-8", errors="ignore") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    # Remove non-visible tags
    for tag in soup(["script", "style", "meta", "noscript"]):
        tag.extract()

    text = soup.get_text(separator="\n")
    text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
    return text

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts text content from a PDF file.
    """
    text = ""
    try:
        with open(pdf_path, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- Page {page_num + 1} ---\n{page_text}"
        
        # Clean up the extracted text
        text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
        return text
    except Exception as e:
        return f"Error extracting PDF: {str(e)}"


def read_support_doc(path: str) -> str:
    
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def build_processed_dataset(
    html_dir="data/html",
    docs_dir="data/uploads",
    out_path="data/processed/combined.txt"
):
    """
    Converts all uploaded HTML files + support docs → single clean text file.
    """
    combined = ""

    # Handle HTML files
    for file in os.listdir(html_dir):
        if file.endswith(".html"):
            content = extract_text_from_html(os.path.join(html_dir, file))
            combined += f"\n\n### HTML FILE: {file}\n{content}\n"

    # Handle support documents
    for file in os.listdir(docs_dir):
        ext = file.split(".")[-1].lower()

        if ext == 'pdf':
            content = extract_text_from_pdf(os.path.join(docs_dir,file))
            combined += f"\n\n### PDF DOC: {file}\n{content}\n"

        elif ext in ["txt", "md", "json"]:
            content = read_support_doc(os.path.join(docs_dir, file))
            combined += f"\n\n### SUPPORT DOC: {file}\n{content}\n"

    
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(combined)

    return combined
