"""
DISABLED Admin Endpoints for Cache Management

These endpoints were disabled in main.py to prevent public access.
They can be re-enabled when proper authentication is implemented.

To re-enable:
1. Add authentication middleware (e.g., API key, OAuth, JWT)
2. Import this module in main.py
3. Include these routes with authentication dependencies

Example:
    from fastapi import Depends
    from auth import verify_admin_token

    @app.get("/api/cache/health", dependencies=[Depends(verify_admin_token)])
    def cache_health():
        ...
"""

from fastapi import HTTPException
import logging

from config import settings
from services.cache_service import cache_service

logger = logging.getLogger(__name__)


# Cache health endpoint
async def cache_health():
    """Get cache health status."""
    try:
        health_status = cache_service.health_check()
        return health_status
    except Exception as e:
        logger.error(f"Cache health check error: {e}")
        return {"status": "error", "healthy": False, "error": str(e)}


# Cache statistics endpoint
async def cache_stats():
    """Get cache statistics and metrics."""
    try:
        stats = cache_service.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        return {"enabled": False, "status": "error", "error": str(e)}


# Clear all cache endpoint
async def clear_cache():
    """Clear all geographic search cache entries."""
    try:
        pattern = f"{settings.cache_key_prefix}:*"
        cleared_keys = cache_service.clear_pattern(pattern)
        logger.info(f"Cleared {cleared_keys} cache keys")
        return {
            "success": True,
            "message": f"Cleared {cleared_keys} cache entries",
            "pattern": pattern
        }
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        return {"success": False, "error": str(e)}


# Clear cache by type endpoint
async def clear_cache_by_type(search_type: str):
    """Clear cache entries for a specific search type."""
    try:
        if search_type.lower() not in ['cp', 'localidad', 'calle']:
            raise HTTPException(
                status_code=400,
                detail="Invalid search type. Use: cp, localidad, or calle"
            )

        pattern = f"{settings.cache_key_prefix}:{settings.cache_version}:{search_type.lower()}:*"
        cleared_keys = cache_service.clear_pattern(pattern)
        logger.info(f"Cleared {cleared_keys} cache keys for type {search_type}")
        return {
            "success": True,
            "message": f"Cleared {cleared_keys} cache entries for type {search_type}",
            "pattern": pattern
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cache clear by type error: {e}")
        return {"success": False, "error": str(e)}


# Cache warming endpoint (placeholder)
async def warm_cache():
    """Warm cache with common searches (for future implementation)."""
    return {
        "success": True,
        "message": "Cache warming functionality not yet implemented",
        "note": "This endpoint is reserved for future cache warming strategies"
    }


# Example of how to register these endpoints with authentication:
"""
from fastapi import APIRouter, Depends
from auth import verify_admin_token

admin_router = APIRouter(
    prefix="/api/admin",
    dependencies=[Depends(verify_admin_token)],
    tags=["admin"]
)

admin_router.get("/cache/health")(cache_health)
admin_router.get("/cache/stats")(cache_stats)
admin_router.delete("/cache/clear")(clear_cache)
admin_router.delete("/cache/clear/{search_type}")(clear_cache_by_type)
admin_router.post("/cache/warm")(warm_cache)

# In main.py:
# app.include_router(admin_router)
"""
