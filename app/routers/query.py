import time
import logging
import json
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from app.models.schemas import QueryRequest, QueryResponse, SourceCitation
from app.models.document import get_all_documents, get_document
from app.services.retrieval import retrieve_context
from app.services.generation import generate_answer, stream_answer
from app.services.cache import generate_cache_key, get_cached_response, set_cached_response

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    start_time = time.perf_counter()
    
    # Test Case 7 check: Query with no documents uploaded
    all_docs = get_all_documents()
    if not all_docs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No documents have been uploaded yet. Please upload a document before querying."
        )
        
    # Test Case 8 check: Query with document_id filter (check if it exists)
    if request.document_id:
        doc = get_document(request.document_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID '{request.document_id}' not found."
            )
            
    # Generate cache key
    cache_key = generate_cache_key(
        question=request.question,
        document_id=request.document_id,
        top_k=request.top_k
    )
    
    # Try cache
    cached = get_cached_response(cache_key)
    if cached:
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return QueryResponse(
            answer=cached["answer"],
            sources=[SourceCitation(**s) for s in cached["sources"]],
            cached=True,
            latency_ms=latency_ms
        )
        
    try:
        # Retrieve context
        context = retrieve_context(
            query=request.question,
            document_id=request.document_id,
            top_k=request.top_k
        )
        
        # Generate answer
        answer = generate_answer(request.question, context)
        
        # Format sources
        sources = [
            SourceCitation(
                document=doc.metadata.get("filename", "Unknown"),
                page=doc.metadata.get("page"),
                chunk_preview=doc.metadata.get("chunk_preview", doc.page_content[:200])
            )
            for doc in context
        ]
        
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        
        response_data = {
            "answer": answer,
            "sources": [s.model_dump() for s in sources],
            "cached": False,
            "latency_ms": latency_ms
        }
        
        # Cache the result
        set_cached_response(cache_key, response_data)
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            cached=False,
            latency_ms=latency_ms
        )
        
    except Exception as e:
        logger.error(f"Error processing query '{request.question}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}"
        )

@router.post("/query/stream")
async def query_documents_stream(request: QueryRequest):
    all_docs = get_all_documents()
    if not all_docs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No documents have been uploaded yet. Please upload a document before querying."
        )
        
    if request.document_id:
        doc = get_document(request.document_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID '{request.document_id}' not found."
            )
            
    try:
        context = retrieve_context(
            query=request.question,
            document_id=request.document_id,
            top_k=request.top_k
        )
        
        def event_generator():
            sources = [
                {
                    "document": doc.metadata.get("filename", "Unknown"),
                    "page": doc.metadata.get("page"),
                    "chunk_preview": doc.metadata.get("chunk_preview", doc.page_content[:200])
                }
                for doc in context
            ]
            yield f"event: sources\ndata: {json.dumps(sources)}\n\n"
            
            for token in stream_answer(request.question, context):
                yield f"event: token\ndata: {json.dumps({'content': token})}\n\n"
                
            yield "event: end\ndata: [DONE]\n\n"
            
        return StreamingResponse(event_generator(), media_type="text/event-stream")
        
    except Exception as e:
        logger.error(f"Error processing streaming query '{request.question}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process streaming query: {str(e)}"
        )
