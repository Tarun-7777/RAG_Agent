import logging
import redis
from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client = None
_redis_available = False

def get_redis_client() -> redis.Redis | None:
    global _redis_client, _redis_available
    if _redis_client is None:
        try:
            logger.info(f"Connecting to Redis at {settings.REDIS_URL}...")
            client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2.0,
                socket_timeout=2.0
            )
            client.ping()
            _redis_client = client
            _redis_available = True
            logger.info("Connected to Redis successfully.")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis. Caching will be disabled. Error: {e}")
            _redis_client = None
            _redis_available = False
            
    return _redis_client

def is_redis_available() -> bool:
    # Trigger connection attempt if not run yet
    get_redis_client()
    return _redis_available
