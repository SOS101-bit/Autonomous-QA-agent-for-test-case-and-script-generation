import os
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Tuple

embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


FAISS_INDEX_PATH = "data/vector_store.index"


CHUNKS_FILE = "data/chunks.txt"


def chunk_text(text: str, chunk_size=500, overlap=50) -> List[str]:
    """
    Very simple chunking function.
    Splits text into overlapping blocks.
    """
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


def build_faiss_index(full_text: str):
    """
    Build FAISS vector DB from processed text.
    """

    # 1. Chunk the text
    chunks = chunk_text(full_text)

    # 2. Generate embeddings
    embeddings = embedding_model.encode(chunks)

    # 3. Create FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    # 4. Save FAISS index to disk
    faiss.write_index(index, FAISS_INDEX_PATH)

    # 5. Save chunks to file
    os.makedirs("data", exist_ok=True)
    with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(c + "\n-----CHUNK_SEPARATOR-----\n")

    return {
        "message": "FAISS index built successfully",
        "num_chunks": len(chunks)
    }


def load_faiss_index():
    """Load FAISS index + chunks when needed."""
    if not os.path.exists(FAISS_INDEX_PATH):
        return None, []

    index = faiss.read_index(FAISS_INDEX_PATH)

    # load chunks back
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        raw = f.read()
        chunks = raw.split("-----CHUNK_SEPARATOR-----\n")
        chunks = [c.strip() for c in chunks if c.strip()]

    return index, chunks


def search_vector_db(query: str, top_k=5) -> List[Tuple[str, float]]:
    """Search FAISS db and return nearest chunks."""

    index, chunks = load_faiss_index()
    if index is None:
        return ["Vector DB not found. Build knowledge base first."]

    # embed query
    query_emb = embedding_model.encode([query])

    # search FAISS
    distances, indices = index.search(query_emb, top_k)

    results = []
    for idx, dist in zip(indices[0], distances[0]):
        results.append((chunks[idx], float(dist)))

    return results
