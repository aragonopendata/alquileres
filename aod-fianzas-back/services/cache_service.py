import json
import logging
from typing import Optional, Dict, Any
from redis import Redis, ConnectionError as RedisConnectionError
from config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching service for geographic search results."""
    
    def __init__(self):
        """Initialize Redis client with configuration from settings."""
        self.redis: Optional[Redis] = None
        self.enabled = settings.redis_enabled
        
        if self.enabled:
            try:
                self.redis = Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    password=settings.redis_password if settings.redis_password else None,
                    db=settings.redis_db,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    retry_on_timeout=True
                )
                # Test connection
                self.redis.ping()
                logger.info(f"Redis connection established: {settings.redis_host}:{settings.redis_port}")
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                self.enabled = False
                self.redis = None
    
    def get_cache_key(self, search_type: str, search_term: str) -> str:
        """Generate normalized cache key for search parameters."""
        normalized_term = search_term.lower().strip().replace(" ", "_")
        return f"{settings.cache_key_prefix}:{settings.cache_version}:{search_type}:{normalized_term}"
    
    def get_ttl_for_search_type(self, search_type: str) -> int:
        """Get appropriate TTL based on search type."""
        ttl_mapping = {
            "cp": settings.cache_cp_ttl,
            "localidad": settings.cache_localidad_ttl, 
            "calle": settings.cache_calle_ttl
        }
        return ttl_mapping.get(search_type.lower(), settings.cache_default_ttl)
    
    def should_cache_error(self, error_message: str) -> bool:
        """Determine if an error response should be cached."""
        # Don't cache service timeout or unavailability errors
        error_msg_lower = error_message.lower()
        no_cache_keywords = [
            'temporalmente no disponibles',  # Spanish: temporarily unavailable
            'timeout', 'timed out', 'connection', 'network', 'unavailable'
        ]
        return not any(keyword in error_msg_lower for keyword in no_cache_keywords)
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve data from cache."""
        if not self.enabled or not self.redis:
            return None
            
        try:
            data = self.redis.get(key)
            if data:
                result = json.loads(data)
                logger.debug(f"Cache HIT for key: {key}")
                return result
            else:
                logger.debug(f"Cache MISS for key: {key}")
                return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Dict[str, Any], ttl: int) -> bool:
        """Store data in cache with TTL."""
        if not self.enabled or not self.redis:
            return False
            
        try:
            serialized_value = json.dumps(value, ensure_ascii=False)
            result = self.redis.setex(key, ttl, serialized_value)
            logger.debug(f"Cache SET for key: {key}, TTL: {ttl}s")
            return result
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete data from cache."""
        if not self.enabled or not self.redis:
            return False
            
        try:
            result = self.redis.delete(key)
            logger.debug(f"Cache DELETE for key: {key}")
            return bool(result)
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.enabled or not self.redis:
            return False
            
        try:
            return bool(self.redis.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        if not self.enabled or not self.redis:
            return 0
            
        try:
            keys = self.redis.keys(pattern)
            if keys:
                result = self.redis.delete(*keys)
                logger.info(f"Cache cleared {result} keys matching pattern: {pattern}")
                return result
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.enabled or not self.redis:
            return {"enabled": False, "status": "disabled"}
            
        try:
            info = self.redis.info()
            stats = {
                "enabled": True,
                "status": "connected",
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "expired_keys": info.get("expired_keys", 0)
            }
            
            # Calculate hit ratio
            hits = stats["keyspace_hits"]
            misses = stats["keyspace_misses"]
            total = hits + misses
            stats["hit_ratio"] = (hits / total * 100) if total > 0 else 0
            
            return stats
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"enabled": True, "status": "error", "error": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on Redis connection."""
        if not self.enabled:
            return {"status": "disabled", "healthy": False}
            
        try:
            if self.redis:
                latency_start = __import__('time').time()
                self.redis.ping()
                latency = (__import__('time').time() - latency_start) * 1000
                
                return {
                    "status": "healthy",
                    "healthy": True,
                    "latency_ms": round(latency, 2),
                    "host": settings.redis_host,
                    "port": settings.redis_port
                }
            else:
                return {"status": "disconnected", "healthy": False}
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {"status": "unhealthy", "healthy": False, "error": str(e)}


# Global cache service instance  
cache_service = CacheService() 