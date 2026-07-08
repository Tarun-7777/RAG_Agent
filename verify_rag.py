import os
import time
from dotenv import load_dotenv
load_dotenv()

from app.services.ingestion import ingest_document
from app.services.retrieval import retrieve_context
from app.services.generation import generate_answer
from app.models.document import get_all_documents

def run_verification():
    print("--- RAG Integration Verification ---")
    
    # 1. Create a sample text document
    sample_text = """
    DocMind is a high-performance Retrieval-Augmented Generation system.
    It supports ingestion of PDF and TXT files.
    The system was successfully deployed on Windows in July 2026.
    The primary developer of DocMind is Tarun from JSS Science and Technology University.
    DocMind uses Pinecone for vector storage and Google Gemini for answering questions.
    """
    
    filename = "docmind_verification.txt"
    file_bytes = sample_text.encode("utf-8")
    
    print(f"\n1. Ingesting text document '{filename}'...")
    try:
        doc_id, chunk_count = ingest_document(file_bytes, filename)
        print(f"SUCCESS: Document ingested! ID: {doc_id}, Chunks: {chunk_count}")
    except Exception as e:
        print(f"FAILED during ingestion: {e}")
        return

    # Wait a moment for Pinecone index replication
    print("\nWaiting 8 seconds for Pinecone vector indexing to replicate...")
    time.sleep(8)

    # 2. Retrieve documents list
    print("\n2. Checking registered documents...")
    docs = get_all_documents()
    print("Registered documents in DB:")
    for d in docs:
        print(f" - ID: {d.document_id}, Filename: {d.filename}, Chunks: {d.chunk_count}")

    # 3. Perform a query
    question = "Who is the primary developer of DocMind and what university is he from?"
    print(f"\n3. Querying system: '{question}'...")
    try:
        context = retrieve_context(question, document_id=doc_id)
        print(f"Retrieved {len(context)} context chunks.")
        for idx, doc in enumerate(context):
            print(f"  [{idx + 1}] Source Preview: {doc.page_content[:100]}")
            
        answer = generate_answer(question, context)
        print(f"\nGenerated Answer:\n{answer}")
        
        # Check response correctness
        if "Tarun" in answer or "JSS" in answer:
            print("\nSUCCESS: The answer correctly retrieved and summarized the context using Google Gemini and Pinecone!")
        else:
            print("\nWARNING: The answer did not contain the expected keywords. Please check LLM output.")
    except Exception as e:
        print(f"FAILED during retrieval or generation: {e}")

if __name__ == "__main__":
    run_verification()
