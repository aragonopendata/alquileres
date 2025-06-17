from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
import logging
from datetime import datetime

from config import settings
from models import LocationSearchRequest, PublicLocationSearchRequest, LocationSearchResponse, HealthStatus
from services.geographic_search_service import GeographicSearchService
from services.cache_service import cache_service
from database2 import query_municipalities, query_streets_by_municipality, \
    query_stats_by_street_and_municipality, DBException

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AOD Fianzas Backend API",
    description="Backend API for Aragon rental deposit data with geographic search capabilities",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Initialize services
geographic_search_service = GeographicSearchService()


@app.get("/")
def root():
    """Redirect to API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthStatus)
def health_check():
    """Health check endpoint for service monitoring."""
    try:
        # Test database connection
        municipalities = query_municipalities()
        db_status = "healthy" if municipalities else "unhealthy"
        
        # Test IGEAR services (basic connectivity)
        igear_status = "healthy"  # Could add actual health checks here
        
        # Test cache connection
        cache_health = cache_service.health_check()
        cache_status = "healthy" if cache_health.get("healthy", False) else "degraded"
        
        overall_status = "healthy"
        if cache_status != "healthy" or db_status != "healthy":
            overall_status = "degraded"
        
        return HealthStatus(
            status=overall_status,
            timestamp=datetime.utcnow().isoformat(),
            services={
                "database": db_status,
                "igear_services": igear_status,
                "cache": cache_status
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthStatus(
            status="unhealthy",
            timestamp=datetime.utcnow().isoformat(),
            services={
                "database": "unhealthy",
                "igear_services": "unknown",
                "cache": "unhealthy"
            }
        )


@app.post("/api/geographic-search", response_model=LocationSearchResponse)
def geographic_search(request: PublicLocationSearchRequest, response: Response):
    """
    Consolidated geographic search endpoint with caching.
    
    Replaces multiple frontend API calls with a single backend endpoint that:
    1. Checks cache for existing results
    2. Detects search type (postal code, municipality, street)
    3. Resolves IGEAR object ID
    4. Performs spatial search
    5. Caches and returns WFS features
    
    Args:
        request: Public geographic search request
        response: FastAPI response object for headers
        
    Returns:
        Location search response with WFS data or error message
    """
    try:
        logger.info(f"Geographic search request: {request.search_text}")
        
        # Convert public request to internal request with hardcoded values
        internal_request = LocationSearchRequest(
            search_text=request.search_text,
            search_type=request.search_type,  # Keep the override option
            layer="fianzas",
            distance=1000
        )
        
        # Check if this will be a cache hit
        search_type = internal_request.search_type or geographic_search_service._detect_search_type(internal_request.search_text)
        cache_key = cache_service.get_cache_key(
            search_type.value.lower(), 
            f"{internal_request.search_text}_{internal_request.layer}_{internal_request.distance}"
        )
        is_cached = cache_service.exists(cache_key)
        
        search_response = geographic_search_service.search_location(internal_request)
        
        # Add cache status header
        response.headers["X-Cache-Status"] = "HIT" if is_cached else "MISS"
        response.headers["X-Cache-Enabled"] = str(cache_service.enabled)
        
        if search_response.success:
            logger.info(f"Search successful for '{internal_request.search_text}': {len(search_response.data.features) if search_response.data else 0} features found")
        else:
            logger.warning(f"Search failed for '{internal_request.search_text}': {search_response.message}")
        
        return search_response
        
    except Exception as e:
        logger.error(f"Geographic search error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during geographic search: {str(e)}"
        )


# Cache administration endpoints
@app.get("/api/cache/health")
def cache_health():
    """Get cache health status."""
    try:
        health_status = cache_service.health_check()
        return health_status
    except Exception as e:
        logger.error(f"Cache health check error: {e}")
        return {"status": "error", "healthy": False, "error": str(e)}


@app.get("/api/cache/stats")
def cache_stats():
    """Get cache statistics and metrics."""
    try:
        stats = cache_service.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        return {"enabled": False, "status": "error", "error": str(e)}


@app.delete("/api/cache/clear")
def clear_cache():
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


@app.delete("/api/cache/clear/{search_type}")
def clear_cache_by_type(search_type: str):
    """Clear cache entries for a specific search type."""
    try:
        if search_type.lower() not in ['cp', 'localidad', 'calle']:
            raise HTTPException(status_code=400, detail="Invalid search type. Use: cp, localidad, or calle")
        
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


@app.post("/api/cache/warm")
def warm_cache():
    """Warm cache with common searches (for future implementation)."""
    return {
        "success": True,
        "message": "Cache warming functionality not yet implemented",
        "note": "This endpoint is reserved for future cache warming strategies"
    }


# Existing endpoints - keep unchanged for backwards compatibility
@app.get("/municipality")
def get_municipalities():
    """Get list of municipalities with rental data."""
    try:
        municipalities = query_municipalities()
        logger.info(f"Retrieved {len(municipalities)} municipalities")
        return municipalities
    except Exception as e:
        logger.error(f"Error retrieving municipalities: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving municipalities")


@app.get("/municipality/{municipality}/street")
def get_streets_by_municipality(municipality: str):
    """Get list of streets for a specific municipality."""
    try:
        streets = query_streets_by_municipality(municipality)
        logger.info(f"Retrieved {len(streets)} streets for municipality '{municipality}'")
        return streets
    except Exception as e:
        logger.error(f"Error retrieving streets for municipality '{municipality}': {e}")
        raise HTTPException(status_code=500, detail="Error retrieving streets")


@app.get("/municipality/{municipality}/street/{street}/stats")
def get_stats_by_municipality_street(municipality: str, street: str):
    """Get rental statistics for a specific municipality and street."""
    try:
        stats = query_stats_by_street_and_municipality(street, municipality)
        logger.info(f"Retrieved {len(stats)} stats for '{street}' in '{municipality}'")
        return stats
    except DBException as e:
        logger.error(f"Database error for stats query: {e.message}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Error retrieving stats for '{street}' in '{municipality}': {e}")
        raise HTTPException(status_code=500, detail="Error retrieving statistics")
