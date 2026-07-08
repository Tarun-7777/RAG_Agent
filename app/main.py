import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.models.document import init_db
from app.core.redis_client import get_redis_client
from app.routers import upload, query

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing SQLite database...")
    init_db()
    
    logger.info("Attempting connection to Redis...")
    get_redis_client()
    yield

app = FastAPI(
    title="DocMind — Intelligent Document Q&A API",
    description="A production-ready RAG backend using FastAPI, LangChain, Google Gemini, Pinecone, and Redis.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)
app.include_router(query.router)

@app.get("/")
def read_root():
    return {
        "name": "DocMind — Intelligent Document Q&A API",
        "status": "healthy",
        "env": settings.APP_ENV
    }
