import os
import logging
from typing import List
from chromadb import PersistentClient
from ollama import Client as OllamaClient
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOCUMENTS_DIR = os.path.join(SCRIPT_DIR, "team_docs")
CHROMA_PERSIST_DIR = os.path.join(SCRIPT_DIR, "chroma_db")
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

def load_documents(doc_dir: str) -> List[str]:
    documents = []
    for root, _, files in os.walk(doc_dir):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                if file.lower().endswith(".txt"):
                    with open(file_path, "r", encoding="utf-8") as f:
                        documents.append(f.read())
                elif file.lower().endswith(".pdf"):
                    from PyPDF2 import PdfReader
                    reader = PdfReader(file_path)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() or ""
                    documents.append(text)
                elif file.lower().endswith(".docx"):
                    from docx import Document
                    doc = Document(file_path)
                    text = "\n".join([p.text for p in doc.paragraphs])
                    documents.append(text)
                else:
                    logger.warning(f"Unsupported file type: {file_path}")
            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")
    logger.info(f"Loaded {len(documents)} documents from {doc_dir}")
    return documents

def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    chunks = []
    start = 0
    text_length = len(text)
    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - chunk_overlap
    return chunks

def embed_text(text: str, ollama_client) -> List[float]:
    response = ollama_client.embeddings(model='nomic-embed-text', prompt=text)
    return response['embedding']

def main():
    ollama_client = OllamaClient(host='http://localhost:11434')

    chroma_client = PersistentClient(path=CHROMA_PERSIST_DIR)

    try:
        chroma_client.delete_collection(name="team_docs")
    except:
        pass

    collection = chroma_client.create_collection(name="team_docs")

    documents = load_documents(DOCUMENTS_DIR)

    doc_id = 0
    for doc in documents:
        chunks = chunk_text(doc, CHUNK_SIZE, CHUNK_OVERLAP)
        for chunk in chunks:
            try:
                embedding = embed_text(chunk, ollama_client)
                collection.add(
                    documents=[chunk],
                    embeddings=[embedding],
                    ids=[str(doc_id)]
                )
                doc_id += 1
            except Exception as e:
                logger.error(f"Failed to add chunk to collection: {e}")

    logger.info("Document ingestion and embedding storage complete.")

    print("Knowledge Base Assistant is ready. Type your query or 'exit' to quit.")
    while True:
        query = input("Query: ").strip()
        if query.lower() in ("exit", "quit"):
            break
        try:
            query_embedding = embed_text(query, ollama_client)

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=3,
                include=["documents"]
            )
            context_chunks = results['documents'][0]

            messages = [
                {"role": "system", "content": "You are a helpful assistant. Use the provided context to answer the question."},
                {"role": "user", "content": "\n\n".join(context_chunks) + f"\n\nQuestion: {query}"}
            ]

            response = ollama_client.chat(model='llama3', messages=messages)
            print("Answer:", response['message']['content'])
        except Exception as e:
            logger.error(f"Error during query processing: {e}")

if __name__ == "__main__":
    main()
