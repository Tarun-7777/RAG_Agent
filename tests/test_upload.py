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
