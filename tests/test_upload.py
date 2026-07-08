from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)

def test_upload_invalid_extension():
    response = client.post(
        "/upload",
        files={"file": ("test.jpg", b"fake image content", "image/jpeg")}
    )
    assert response.status_code == 422
    assert "Unsupported file type" in response.json()["detail"]

@patch("app.routers.upload.ingest_document")
def test_upload_valid_txt(mock_ingest):
    mock_ingest.return_value = ("doc_test123", 5)
    
    response = client.post(
        "/upload",
        files={"file": ("test.txt", b"hello world content", "text/plain")}
    )
    assert response.status_code == 201
    assert response.json() == {
        "document_id": "doc_test123",
        "filename": "test.txt",
        "chunks_stored": 5,
        "status": "success"
    }

from unittest.mock import MagicMock

def test_delete_document_not_found():
    with patch("app.routers.upload.get_document") as mock_get:
        mock_get.return_value = None
        response = client.delete("/documents/non_existent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

@patch("app.routers.upload.get_document")
@patch("app.routers.upload.delete_document")
@patch("app.routers.upload.get_pinecone_client")
def test_delete_document_success(mock_get_pc, mock_delete, mock_get_doc):
    mock_get_doc.return_value = MagicMock(document_id="doc_123")
    
    mock_pc = MagicMock()
    mock_index = MagicMock()
    mock_pc.Index.return_value = mock_index
    mock_get_pc.return_value = mock_pc
    
    response = client.delete("/documents/doc_123")
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    mock_index.delete.assert_called_once_with(filter={"document_id": "doc_123"})
    mock_delete.assert_called_once_with("doc_123")
