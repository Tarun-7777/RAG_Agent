import logging
from pinecone import Pinecone, ServerlessSpec
from app.core.config import settings

logger = logging.getLogger(__name__)

_pc_client = None

def get_pinecone_client() -> Pinecone:
    global _pc_client
    if _pc_client is None:
        if not settings.PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY is not set in environment or config.")
        _pc_client = Pinecone(api_key=settings.PINECONE_API_KEY)
    return _pc_client

def init_index():
    pc = get_pinecone_client()
    index_name = settings.PINECONE_INDEX_NAME
    
    # Parse PINECONE_ENVIRONMENT (e.g., us-east-1-aws -> region="us-east-1", cloud="aws")
    env = settings.PINECONE_ENVIRONMENT
    cloud = "aws"
    region = "us-east-1"
    if env:
        parts = env.split("-")
        if len(parts) >= 2:
            cloud = parts[-1]
            region = "-".join(parts[:-1])
        else:
            region = env

    existing_indexes = [idx.name for idx in pc.list_indexes()]
    if index_name in existing_indexes:
        desc = pc.describe_index(index_name)
        if desc.dimension != settings.EMBEDDING_DIMENSION:
            logger.info(f"Index dimension mismatch ({desc.dimension} vs {settings.EMBEDDING_DIMENSION}). Recreating index...")
            pc.delete_index(index_name)
            # Remove it so the next block recreates it
            existing_indexes.remove(index_name)
            
    if index_name not in existing_indexes:
        logger.info(f"Creating Pinecone serverless index: {index_name} (region={region}, cloud={cloud}, dimension={settings.EMBEDDING_DIMENSION})")
        pc.create_index(
            name=index_name,
            dimension=settings.EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(
                cloud=cloud,
                region=region
            )
        )
        logger.info(f"Index {index_name} created successfully.")
    else:
        logger.info(f"Pinecone index {index_name} already exists.")

