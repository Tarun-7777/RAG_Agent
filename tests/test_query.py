from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
from app.models.document import add_document, sqlite3, DB_PATH
from langchain_core.documents import Document

client = TestClient(app)

def clean_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS documents")
    conn.commit()
    conn.close()

def test_query_no_documents():
    clean_db()
    response = client.post(
        "/query",
        json={"question": "What is the revenue?", "top_k": 5}
    )
    assert response.status_code == 400
    assert "No documents have been uploaded yet" in response.json()["detail"]

def test_query_document_not_found():
    clean_db()
    add_document("doc_123", "dummy.pdf", 10)
    
    response = client.post(
        "/query",
        json={"question": "What is the revenue?", "document_id": "non_existent_doc"}
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

@patch("app.routers.query.retrieve_context")
@patch("app.routers.query.generate_answer")
@patch("app.routers.query.get_cached_response")
def test_query_success(mock_cache, mock_gen, mock_retrieve):
    clean_db()
    add_document("doc_123", "annual_report.pdf", 1)
    
    mock_cache.return_value = None
    mock_retrieve.return_value = [
        Document(
            page_content="The revenue was $4.2B in Q3.",
            metadata={"filename": "annual_report.pdf", "page": 14, "chunk_preview": "...revenue was $4.2B..."}
        )
    ]
    mock_gen.return_value = "The Q3 revenue was $4.2 billion [1]."
    
    response = client.post(
        "/query",
        json={"question": "What was the revenue?", "document_id": "doc_123"}
    )
    
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["answer"] == "The Q3 revenue was $4.2 billion [1]."
    assert len(res_data["sources"]) == 1
    assert res_data["sources"][0]["document"] == "annual_report.pdf"
    assert res_data["sources"][0]["page"] == 14
    assert res_data["cached"] is False
