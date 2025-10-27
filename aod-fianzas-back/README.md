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

The rental statistics data is fetched from IGEAR WFS service using the included script.

**To update the data:**

```bash
# Navigate to backend directory
cd aod-fianzas-back

# Run the fetch script
python fetch_fianzas_layer.py

# This will:
# 1. Query IGEAR SITA WMS for all fianzas features
# 2. Download ~17MB GeoJSON file (9,332+ features)
# 3. Save as fianzas_wfs_layer.json in the backend root
# 4. Takes ~2-5 minutes depending on network speed

# Restart the service to reload the new data
docker-compose restart aod-fianzas-back
# OR if running locally:
# Press Ctrl+C and run: uvicorn main:app --reload
```

**Script details:**
- **Location**: `fetch_fianzas_layer.py` (in backend root)
- **Source**: IGEAR SITA WMS service (https://idearagon.aragon.es/SITA_WMS)
- **Layer**: `fianzas` (rental deposit data)
- **Format**: GeoJSON (EPSG:25830)
- **Timeout**: 5 minutes (for large dataset)
- **Output**: `fianzas_wfs_layer.json` (~17MB)

**Data Refresh Schedule**: Manual (rental data is relatively static, updates typically quarterly)

**When to update:**
- New rental data is published by Gobierno de Aragón
- Missing streets or municipalities reported
- Data quality issues identified

### Data Structure

The JSON file contains GeoJSON features with:
- **Type**: FeatureCollection with 9,332+ features
- **Geometry**: LineString coordinates for street visualization
- **Properties**:
  - `objectid`: Unique identifier (integer)
  - `via_loc`: Street name and municipality (e.g., "Calle Mayor (Zaragoza)")
  - `valores`: JSON string containing rental statistics array

**Statistics format** (inside `valores` field):
```json
[
  {
    "anyo": 2024,      // Year
    "tipo": 1,         // 1=Vivienda (Housing), 2=Local (Commercial)
    "min": 192.32,     // Minimum rent (€/month)
    "max": 300.51,     // Maximum rent (€/month)
    "media": 238.40,   // Average rent (€/month)
    "num": 3           // Number of deposits
  }
]
```

**Indexes**: Four hash indexes are built automatically on startup for O(1) query performance:
1. Municipality → Streets
2. (Municipality, Street) → Feature
3. ObjectID → Feature
4. Municipalities set (cached)

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
