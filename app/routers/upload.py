import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from app.models.schemas import UploadResponse, DocumentListResponse, DocumentInfo
from app.models.document import get_all_documents
from app.services.ingestion import ingest_document

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
