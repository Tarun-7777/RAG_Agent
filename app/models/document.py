import sqlite3
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel

DB_PATH = "docmind.db"

class DocumentMetadata(BaseModel):
    document_id: str
    filename: str
    uploaded_at: str
    chunk_count: int

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            document_id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            uploaded_at TEXT NOT NULL,
            chunk_count INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def add_document(doc_id: str, filename: str, chunk_count: int) -> DocumentMetadata:
    init_db()
    uploaded_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO documents (document_id, filename, uploaded_at, chunk_count) VALUES (?, ?, ?, ?)",
        (doc_id, filename, uploaded_at, chunk_count)
    )
    conn.commit()
    conn.close()
    return DocumentMetadata(
        document_id=doc_id,
        filename=filename,
        uploaded_at=uploaded_at,
        chunk_count=chunk_count
    )

def get_all_documents() -> List[DocumentMetadata]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT document_id, filename, uploaded_at, chunk_count FROM documents ORDER BY uploaded_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    return [
        DocumentMetadata(
            document_id=row[0],
            filename=row[1],
            uploaded_at=row[2],
            chunk_count=row[3]
        ) for row in rows
    ]

def get_document(doc_id: str) -> Optional[DocumentMetadata]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT document_id, filename, uploaded_at, chunk_count FROM documents WHERE document_id = ?", (doc_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return DocumentMetadata(
            document_id=row[0],
            filename=row[1],
            uploaded_at=row[2],
            chunk_count=row[3]
        )
    return None

def delete_document(doc_id: str) -> bool:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM documents WHERE document_id = ?", (doc_id,))
    changes = conn.total_changes
    conn.commit()
    conn.close()
    return changes > 0
