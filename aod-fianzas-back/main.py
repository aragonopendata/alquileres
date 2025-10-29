from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
import logging
from datetime import datetime

from config import settings
from models import LocationSearchRequest, PublicLocationSearchRequest, LocationSearchResponse, HealthStatus
from services.geographic_search_service import GeographicSearchService
from services.cache_service import cache_service
from services.json_data_service import json_data_service

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
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Initialize services
geographic_search_service = GeographicSearchService()


@app.on_event("startup")
async def startup_event():
    """Log environment configuration on startup."""
    logger.info("=" * 60)
    logger.info(f"Starting AOD Fianzas API")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"IGEAR Domain: {settings.get_igear_domain()}")
    logger.info(f"CORS Origins: {settings.get_cors_origins_list()}")
    logger.info(f"Log Level: {settings.log_level}")
    logger.info(f"Redis: {settings.redis_host}:{settings.redis_port} (enabled: {settings.redis_enabled})")
    logger.info("=" * 60)


@app.get("/")
def root():
    """Redirect to API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthStatus)
def health_check():
    """Health check endpoint for service monitoring."""
    try:
        # Test JSON data service
        municipalities = json_data_service.get_municipalities()
        json_status = "healthy" if municipalities else "unhealthy"

        # Test IGEAR services (basic connectivity)
        igear_status = "healthy"  # Could add actual health checks here

        # Test cache connection
        cache_health = cache_service.health_check()
        cache_status = "healthy" if cache_health.get("healthy", False) else "degraded"

        overall_status = "healthy"
        if cache_status != "healthy" or json_status != "healthy":
            overall_status = "degraded"

        return HealthStatus(
            status=overall_status,
            timestamp=datetime.utcnow().isoformat(),
            services={
                "json_data": json_status,
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
                "json_data": "unhealthy",
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


# Note: Admin endpoints for cache management have been moved to admin_endpoints_disabled.py
# They can be re-enabled when proper authentication is implemented.
# See admin_endpoints_disabled.py for details.

# Public API endpoints
@app.get("/municipality")
def get_municipalities():
    """Get list of municipalities with rental data from JSON."""
    try:
        municipalities = json_data_service.get_municipalities()
        logger.info(f"Retrieved {len(municipalities)} municipalities")
        return municipalities
    except Exception as e:
        logger.error(f"Error retrieving municipalities: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving municipalities")


@app.get("/municipality/{municipality}/street")
def get_streets_by_municipality(municipality: str, response: Response):
    """Get list of streets for a specific municipality from JSON."""
    try:
        streets = json_data_service.get_streets_by_municipality(municipality)

        # Add informational header
        response.headers["X-Streets-Source"] = "JSON"

        logger.info(f"Retrieved {len(streets)} streets for municipality '{municipality}' from JSON")
        return streets

    except Exception as e:
        logger.error(f"Error retrieving streets for municipality '{municipality}': {e}")
        raise HTTPException(status_code=500, detail="Error retrieving streets")


@app.get("/municipality/{municipality}/street/{street}/stats")
def get_stats_by_municipality_street(municipality: str, street: str):
    """Get rental statistics for a specific municipality and street from JSON."""
    try:
        stats = json_data_service.get_stats_by_street_and_municipality(street, municipality)
        logger.info(f"Retrieved {len(stats)} stats for '{street}' in '{municipality}'")
        return stats
    except Exception as e:
        logger.error(f"Error retrieving stats for '{street}' in '{municipality}': {e}")
        raise HTTPException(status_code=500, detail="Error retrieving statistics")
