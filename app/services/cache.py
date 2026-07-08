import hashlib
import json
import logging
from typing import Optional, Dict, Any
from app.core.redis_client import get_redis_client, is_redis_available
from app.core.config import settings

logger = logging.getLogger(__name__)

# Resilient fallback memory cache
_memory_cache: Dict[str, Any] = {}

def generate_cache_key(question: str, document_id: Optional[str] = None, top_k: Optional[int] = None) -> str:
    payload = {
        "question": question.strip().lower(),
        "document_id": document_id,
        "top_k": top_k or settings.TOP_K_CHUNKS
    }
    serialized = json.dumps(payload, sort_keys=True)
    hash_val = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return f"docmind:cache:{hash_val}"

def get_cached_response(key: str) -> Optional[Dict[str, Any]]:
    if is_redis_available():
        client = get_redis_client()
        if client:
            try:
                cached = client.get(key)
                if cached:
                    logger.info(f"Cache HIT (Redis) for key {key}")
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Failed to read from Redis: {e}")
                
    if key in _memory_cache:
        logger.info(f"Cache HIT (In-Memory) for key {key}")
        return _memory_cache[key]
        
    logger.info(f"Cache MISS for key {key}")
    return None

def set_cached_response(key: str, data: Dict[str, Any]):
    if is_redis_available():
        client = get_redis_client()
        if client:
            try:
                client.setex(
                    key,
                    settings.REDIS_TTL_SECONDS,
                    json.dumps(data)
                )
                logger.info(f"Cached response in Redis for key {key}")
                return
            except Exception as e:
                logger.warning(f"Failed to write to Redis: {e}")
                
    _memory_cache[key] = data
    logger.info(f"Cached response in memory for key {key}")
