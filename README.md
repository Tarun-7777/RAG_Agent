# 🧠 DocMind — Intelligent Document Q&A API

A production-ready **Retrieval-Augmented Generation (RAG)** backend that lets users upload documents and ask natural language questions against them — with cited, grounded answers.

Built with **FastAPI · LangChain · Google Gemini 2.5 · Pinecone · Redis · Python 3.11+**

---

## 🎯 What It Does

1. **Upload** a PDF or `.txt` document via REST API
2. **Ingest** — chunking, embedding, and storing vectors in Pinecone
3. **Query** — ask a natural language question; the system retrieves relevant chunks and generates a grounded answer using Gemini 2.5
4. **Cite** — every answer includes source chunk references (page numbers, doc name)
5. **Cache** — repeated queries are served from Redis in milliseconds

---

## 🏗️ Architecture

```
Client
  │
  ▼
FastAPI (REST API)
  ├── POST /upload       → Ingest pipeline
  │     ├── PDF/text parser (PyMuPDF / plain text)
  │     ├── Text chunker (RecursiveCharacterTextSplitter)
  │     ├── Embeddings (Google text-embedding-004)
  │     └── Vector upsert → Pinecone
  │
  ├── POST /query        → RAG pipeline
  │     ├── Redis cache check
  │     ├── Embed query → Pinecone similarity search (top-k chunks)
  │     ├── Prompt builder (query + retrieved context)
  │     ├── Gemini 2.5 Flash → answer generation
  │     └── Return answer + sources
  │
  └── GET  /documents    → List all uploaded docs
```

---

## 📁 Project Structure

```
docmind/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── routers/
│   │   ├── upload.py        # Document ingestion endpoint
│   │   └── query.py         # Q&A endpoint
│   ├── services/
│   │   ├── ingestion.py     # Chunking + embedding + Pinecone upsert
│   │   ├── retrieval.py     # Vector search + context assembly
│   │   ├── generation.py    # Gemini 2.5 prompt + answer generation
│   │   └── cache.py         # Redis caching layer
│   ├── models/
│   │   ├── schemas.py       # Pydantic request/response models
│   │   └── document.py      # Document metadata model
│   └── core/
│       ├── config.py        # Settings (env vars via pydantic-settings)
│       ├── pinecone_client.py
│       └── redis_client.py
├── tests/
│   ├── test_upload.py
│   ├── test_query.py
│   └── test_cache.py
├── sample_docs/
│   └── sample.pdf           # Test document for manual testing
├── .env.example
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## ⚙️ Setup & Installation

### 1. Prerequisites

- Python 3.11+
- A [Pinecone](https://www.pinecone.io/) account (free tier works)
- A [Google AI Studio](https://aistudio.google.com/) API key (Gemini 2.5)
- Redis (local via Docker, or [Upstash](https://upstash.com/) for free hosted)

### 2. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/docmind.git
cd docmind
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment Variables

Copy `.env.example` to `.env` and fill in your keys:

```env
# Google Gemini
GEMINI_API_KEY=your_gemini_api_key_here

# Pinecone
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=docmind-index
PINECONE_ENVIRONMENT=us-east-1-aws   # or your region

# Redis
REDIS_URL=redis://localhost:6379
REDIS_TTL_SECONDS=3600

# App
APP_ENV=development
TOP_K_CHUNKS=5
CHUNK_SIZE=500
CHUNK_OVERLAP=50
```

### 4. Initialize Pinecone Index

```bash
python -c "
from app.core.pinecone_client import init_index
init_index()
print('Pinecone index ready.')
"
```

### 5. Run the API

```bash
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for the interactive Swagger UI.

---

## 🔌 API Reference

### `POST /upload`

Upload a document for ingestion.

**Request:** `multipart/form-data`

| Field | Type   | Description              |
|-------|--------|--------------------------|
| file  | File   | PDF or `.txt` file       |

**Response:**
```json
{
  "document_id": "doc_abc123",
  "filename": "annual_report.pdf",
  "chunks_stored": 42,
  "status": "success"
}
```

---

### `POST /query`

Ask a question against uploaded documents.

**Request:** `application/json`
```json
{
  "question": "What was the revenue in Q3?",
  "document_id": "doc_abc123",   // optional — omit to search all docs
  "top_k": 5
}
```

**Response:**
```json
{
  "answer": "The Q3 revenue was $4.2 billion, representing a 12% YoY increase.",
  "sources": [
    {
      "document": "annual_report.pdf",
      "page": 14,
      "chunk_preview": "...Q3 results showed revenue of $4.2B..."
    }
  ],
  "cached": false,
  "latency_ms": 820
}
```

---

### `GET /documents`

List all ingested documents.

**Response:**
```json
{
  "documents": [
    {
      "document_id": "doc_abc123",
      "filename": "annual_report.pdf",
      "uploaded_at": "2025-07-08T10:30:00Z",
      "chunk_count": 42
    }
  ]
}
```

---

## 🧪 Testing

Run the full test suite:

```bash
pytest tests/ -v
```

### Test Checklist (for manual/automated verification)

| # | Test Case | Expected Outcome |
|---|-----------|-----------------|
| 1 | Upload a valid PDF | `chunks_stored > 0`, status `success` |
| 2 | Upload a `.txt` file | Same as above |
| 3 | Upload an unsupported file type (`.jpg`) | `422 Unprocessable Entity` |
| 4 | Query with a relevant question | Answer references content from the doc |
| 5 | Query with an irrelevant question | Model responds with "not found in context" |
| 6 | Query the same question twice | Second response has `"cached": true` |
| 7 | Query with no documents uploaded | Graceful error message |
| 8 | Query with `document_id` filter | Only searches that doc's chunks |

---

## 📦 Requirements

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
python-multipart==0.0.9
langchain==0.2.5
langchain-google-genai==1.0.6
langchain-pinecone==0.1.1
pinecone-client==3.2.2
google-generativeai==0.7.2
pymupdf==1.24.5
redis==5.0.4
pydantic-settings==2.2.1
python-dotenv==1.0.1
pytest==8.2.2
httpx==0.27.0
```

---

## 🚀 Stretch Goals (to level it up)

- [ ] **Multi-document chat** — maintain conversation history across turns using LangGraph
- [ ] **Streaming responses** — Server-Sent Events (SSE) for real-time answer generation
- [ ] **Hybrid search** — combine BM25 keyword search with vector similarity (Pinecone hybrid)
- [ ] **Re-ranking** — use Cohere or a cross-encoder to reorder retrieved chunks before generation
- [ ] **Dockerize** — `docker-compose up` to spin up the full stack (API + Redis)
- [ ] **Deploy to AWS** — EC2 + ECR, or Lambda via Mangum adapter
- [ ] **Evaluation** — RAGAS metrics (faithfulness, answer relevancy, context recall)

---

## 💡 Key Concepts Demonstrated

| Concept | Implementation |
|---------|---------------|
| **Chunking strategy** | `RecursiveCharacterTextSplitter` with overlap |
| **Embedding model** | Google `text-embedding-004` (768-dim) |
| **Vector store** | Pinecone serverless index |
| **Generation model** | Gemini 2.5 Flash with grounded prompting |
| **Caching** | Redis with query-hash as key |
| **API design** | FastAPI with Pydantic validation |
| **Source citation** | Chunk metadata returned alongside answer |

---


