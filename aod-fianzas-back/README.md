# AOD Fianzas Backend API

FastAPI backend service for Aragon rental deposit data with geographic search capabilities.

## Features

- **Geographic Search**: Unified search endpoint for postal codes, municipalities, and streets
- **IGEAR Integration**: Connects to Aragon's geographic information services
- **Redis Caching**: Configurable caching layer for improved performance
- **JSON Data Layer**: High-performance in-memory data with O(1) lookup indexes
- **Health Monitoring**: Health check endpoints for service monitoring

## Performance

The backend uses an optimized JSON data layer with hash indexes:
- **Data**: 9,332 street features loaded from `fianzas_wfs_layer.json`
- **Startup**: ~0.7s to load and index data
- **Memory**: ~18MB per worker (17MB data + 1MB indexes)
- **Query Speed**: 5-20 microseconds (1000-6000x faster than database queries)

## API Endpoints

### Core Endpoints
- `GET /` - API documentation (redirects to `/docs`)
- `GET /health` - Service health check
- `POST /api/geographic-search` - Consolidated geographic search

### Data Endpoints
- `GET /municipality` - List all municipalities
- `GET /municipality/{municipality}/street` - Streets by municipality
- `GET /municipality/{municipality}/street/{street}/stats` - Rental statistics

### Cache Management
- `GET /api/cache/health` - Cache health status
- `GET /api/cache/stats` - Cache statistics
- `DELETE /api/cache/clear` - Clear all cache
- `DELETE /api/cache/clear/{search_type}` - Clear cache by type

## Quick Start

### Using Docker
```bash
docker build -t aod-fianzas-back .
docker run -p 8000:8000 aod-fianzas-back
```

### Local Development
```bash
# Install dependencies with uv
pip install uv
uv sync

# Run the application
uvicorn main:app --reload
```

## Configuration

Environment variables (see `config.py`):
- `REDIS_HOST` - Redis server host
- `REDIS_PORT` - Redis server port
- `CORS_ORIGINS` - Allowed CORS origins
- `LOG_LEVEL` - Logging level

## Data Management

### Updating the JSON Data

The rental statistics data is fetched from IGEAR WFS service:

```bash
# Fetch latest data from IGEAR
cd aod-fianzas-back/scripts
python fetch_fianzas_layer.py

# This creates/updates: fianzas_wfs_layer.json
# Restart the service to reload data
```

**Data Refresh Schedule**: Manual (data is relatively static)

### Data Structure

The JSON file contains GeoJSON features with:
- Street geometries (LineStrings)
- `via_loc`: Street name and municipality
- `valores`: Rental statistics (JSON array)
- `objectid`: Unique identifier

Indexes are built automatically on startup for instant lookups.

## Dependencies

- FastAPI - Web framework
- Redis - Caching layer
- HTTPX - HTTP client for IGEAR services
- Pydantic - Data validation
- lxml - XML processing for IGEAR responses
- python-dotenv - Environment configuration

## Architecture

The application follows a service-oriented architecture:

### Core Services
- **`JsonDataService`**: In-memory JSON data with O(1) hash indexes
  - Loads `fianzas_wfs_layer.json` at startup
  - Builds 4 lookup indexes: municipality→streets, (municipality,street)→feature, objectid→feature, municipalities set
  - Provides instant data access (5-20μs queries)

- **`StreetsService`**: High-level wrapper for street and statistics queries
  - Delegates to `JsonDataService`
  - Maintains backward-compatible API

- **`GeographicSearchService`**: Orchestrates geographic search
  - Integrates with IGEAR services
  - Handles postal codes, municipalities, and street searches

- **`CacheService`**: Redis-based caching
  - Caches IGEAR service responses
  - Configurable TTL per search type

- **`IgearService`**: IGEAR platform integration
  - TypedSearchService, SpatialSearchService, SITA WMS
  - Timeout handling and error recovery

### Data Flow
1. **Streets/Stats Requests** → `JsonDataService` (O(1) hash lookup) → Response
2. **Geographic Search** → IGEAR Services → Cache → Response
3. **Data Updates** → `fetch_fianzas_layer.py` → New JSON → Service restart
