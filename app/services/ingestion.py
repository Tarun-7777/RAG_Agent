import uuid
# pyrefly: ignore [missing-import]
import fitz
import logging
from typing import List, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_pinecone import PineconeVectorStore
from app.core.config import settings
from app.models.document import add_document
from app.services.retrieval import get_embeddings

logger = logging.getLogger(__name__)

def extract_pdf_chunks(file_bytes: bytes) -> List[Tuple[str, int]]:
    """Extracts text from PDF page by page and returns list of (text, page_num_1_based)."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages_text = []
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        text = page.get_text()
        pages_text.append((text, page_idx + 1))
    return pages_text

def chunk_text(text: str, page_num: int = 1) -> List[Tuple[str, int]]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP
    )
    chunks = text_splitter.split_text(text)
    return [(chunk, page_num) for chunk in chunks]

def ingest_document(file_bytes: bytes, filename: str) -> Tuple[str, int]:
    doc_id = f"doc_{uuid.uuid4().hex[:8]}"
    
    ext = filename.split(".")[-1].lower()
    all_chunks = []
    
    if ext == "pdf":
        pages = extract_pdf_chunks(file_bytes)
        for text, page_num in pages:
            all_chunks.extend(chunk_text(text, page_num))
    elif ext == "txt":
        text = file_bytes.decode("utf-8", errors="ignore")
        all_chunks.extend(chunk_text(text, 1))
    else:
        raise ValueError(f"Unsupported file format: {ext}")
        
    if not all_chunks:
        return doc_id, 0
        
    docs = []
    for chunk, page_num in all_chunks:
        docs.append(
            Document(
                page_content=chunk,
                metadata={
                    "document_id": doc_id,
                    "filename": filename,
                    "page": page_num,
                    "chunk_preview": chunk[:200].replace("\n", " ").strip()
                }
            )
        )
        
    embeddings = get_embeddings()
    
    BATCH_SIZE = 100
    for i in range(0, len(docs), BATCH_SIZE):
        batch = docs[i : i + BATCH_SIZE]
        logger.info(f"Uploading batch {i // BATCH_SIZE + 1} ({len(batch)} chunks) to Pinecone...")
        PineconeVectorStore.from_documents(
            documents=batch,
            embedding=embeddings,
            index_name=settings.PINECONE_INDEX_NAME,
            pinecone_api_key=settings.PINECONE_API_KEY
        )
    
    # Save metadata
    add_document(doc_id=doc_id, filename=filename, chunk_count=len(docs))
    
    logger.info(f"Ingestion successful: {doc_id} ({len(docs)} chunks stored)")
    return doc_id, len(docs)
