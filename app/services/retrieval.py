import logging
from typing import List, Optional
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from app.core.config import settings

logger = logging.getLogger(__name__)

def retrieve_context(query: str, document_id: Optional[str] = None, top_k: Optional[int] = None) -> List[Document]:
    embeddings = GoogleGenerativeAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        google_api_key=settings.GEMINI_API_KEY
    )
    
    vectorstore = PineconeVectorStore(
        index_name=settings.PINECONE_INDEX_NAME,
        embedding=embeddings,
        pinecone_api_key=settings.PINECONE_API_KEY
    )
    
    k = top_k or settings.TOP_K_CHUNKS
    
    # Formulate filter dictionary for Pinecone
    search_filter = {"document_id": document_id} if document_id else None
    
    logger.info(f"Retrieving top {k} chunks for query. Filter: {search_filter}")
    
    results = vectorstore.similarity_search(query, k=k, filter=search_filter)
    return results
