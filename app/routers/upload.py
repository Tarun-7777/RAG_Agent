import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from app.models.schemas import UploadResponse, DocumentListResponse, DocumentInfo
from app.models.document import get_all_documents, get_document, delete_document
from app.services.ingestion import ingest_document
from app.core.pinecone_client import get_pinecone_client
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...)):
    filename = file.filename
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Filename is missing."
        )
        
    ext = filename.split(".")[-1].lower()
    if ext not in ["pdf", "txt"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type '{ext}'. Only PDF and TXT are supported."
        )
        
    try:
        content = await file.read()
        doc_id, chunks_stored = ingest_document(content, filename)
        return UploadResponse(
            document_id=doc_id,
            filename=filename,
            chunks_stored=chunks_stored,
            status="success"
        )
    except Exception as e:
        logger.error(f"Error ingesting document {filename}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest document: {str(e)}"
        )

@router.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    try:
        docs = get_all_documents()
        documents_info = [
            DocumentInfo(
                document_id=d.document_id,
                filename=d.filename,
                uploaded_at=d.uploaded_at,
                chunk_count=d.chunk_count
            )
            for d in docs
        ]
        return DocumentListResponse(documents=documents_info)
    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}"
        )

@router.delete("/documents/{doc_id}", status_code=status.HTTP_200_OK)
async def delete_document_endpoint(doc_id: str):
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{doc_id}' not found."
        )
        
    try:
        pc = get_pinecone_client()
        index = pc.Index(settings.PINECONE_INDEX_NAME)
        logger.info(f"Deleting vectors from Pinecone for document_id: {doc_id}")
        index.delete(filter={"document_id": doc_id})
        
        delete_document(doc_id)
        
        return {"status": "success", "message": f"Document '{doc_id}' and all its vectors deleted."}
    except Exception as e:
        logger.error(f"Error deleting document {doc_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )
