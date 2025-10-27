# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AOD Fianzas is a full-stack web application that visualizes rental deposit data for Aragon, Spain. The application consists of:

- **Frontend**: Angular 19 application with OpenLayers mapping (`aod-fianzas/`)
- **Backend**: FastAPI service with geographic search capabilities (`aod-fianzas-back/`)
- **Database**: PostgreSQL for rental statistics data
- **Cache**: Redis for performance optimization
- **Data Processing**: Python scripts for data ingestion (`data/`)

## Common Development Commands

### Frontend (Angular - aod-fianzas/)
```bash
cd aod-fianzas
npm install                           # Install dependencies
ng serve                             # Development server (http://localhost:4200)
ng build                             # Build for development
ng build --configuration production --base-href /servicios/alquileres/  # Production build
ng test                              # Run unit tests
ng lint                              # Run linter
ng e2e                               # Run e2e tests
```

### Backend (FastAPI - aod-fianzas-back/)
```bash
cd aod-fianzas-back
pip install uv                       # Install uv package manager
uv sync                              # Install dependencies
uvicorn main:app --reload            # Development server (http://localhost:8000)
python -m pytest                     # Run tests (if available)
```

### Full Stack Development
```bash
docker-compose up                     # Run all services
docker-compose up --build            # Rebuild and run all services
docker-compose down                   # Stop all services
```

### Data Processing
```bash
cd data
uv sync                              # Install dependencies
python main.py                       # Process rental data
```

## Architecture Overview

### Frontend Architecture
- **Framework**: Angular 19 with standalone components
- **Styling**: SCSS + Tailwind CSS
- **Mapping**: OpenLayers for interactive maps
- **State Management**: Angular services with RxJS
- **Key Components**:
  - `MapSearchComponent`: Primary map interface
  - `ListsearchComponent`: Dropdown search interface
  - `MapComponent`: OpenLayers integration
  - `HeaderComponent`: Geographic search input

### Backend Architecture
- **API Framework**: FastAPI with Python
- **Services**: `GeographicSearchService`, `IgearService`, `CacheService`, `JsonDataService`
- **Data Storage**:
  - JSON file (`fianzas_wfs_layer.json`) with O(1) lookup indexes for rental statistics
  - PostgreSQL for legacy compatibility (minimal usage)
- **Caching**: Redis with smart TTL management
- **External Integration**: IGEAR platform services for geographic data
- **Performance**: In-memory hash indexes for instant data access

### Data Flow

#### Geographic Search (Postal codes, municipalities)
1. Frontend sends search requests to `/api/geographic-search`
2. Backend detects search type (postal code, municipality, street)
3. IGEAR services resolve geographic entities and spatial relationships
4. Results cached in Redis and returned to frontend
5. Frontend displays features on OpenLayers map

#### Street Data and Statistics (Optimized)
1. Frontend requests streets or statistics via REST endpoints
2. `JsonDataService` uses O(1) hash lookup indexes (no database queries)
3. Returns data from in-memory JSON (9,332 features loaded at startup)
4. Instant response times (~5-20 microseconds per query)

## Key Services and APIs

### Backend Endpoints

**Public endpoints (visible in `/docs`):**
- `POST /api/geographic-search` - Consolidated geographic search
- `GET /municipality` - List all municipalities
- `GET /municipality/{municipality}/street` - Streets by municipality
- `GET /municipality/{municipality}/street/{street}/stats` - Rental statistics
- `GET /health` - Service health check

**Admin endpoints (currently DISABLED):**
These endpoints are commented out in `main.py` and not accessible:
- `GET /api/cache/health` - Cache health status
- `GET /api/cache/stats` - Cache statistics and metrics
- `DELETE /api/cache/clear` - Clear all cache entries
- `DELETE /api/cache/clear/{search_type}` - Clear cache by type (cp, localidad, calle)
- `POST /api/cache/warm` - Cache warming (placeholder, not implemented)

To re-enable these endpoints, uncomment the relevant sections in `aod-fianzas-back/main.py`.

### Backend Services
- `JsonDataService`: In-memory JSON data with O(1) lookup indexes for streets and statistics
- `GeographicSearchService`: Geographic search coordination
- `IgearService`: IGEAR platform integration for geographic data
- `CacheService`: Redis caching layer
- `StreetsService`: Wrapper for JsonDataService (delegates to JSON indexes)

### Frontend Services
- `AlquileresApiService`: Backend API communication
- `GeographicSearchService`: Geographic search coordination
- `MapService`: OpenLayers map management
- `IgearService`: Direct IGEAR integration (legacy)

## External Dependencies

### IGEAR Platform Services
The application integrates with Aragon's geographic infrastructure:
- **TypedSearchService**: Entity resolution
- **SpatialSearchService**: Spatial queries
- **SITA WMS**: Web Feature Service
- **Visor2D**: 2D visualization data

### Environment Configuration
Key environment variables for backend:
- `DB_URL`: PostgreSQL connection string (legacy, minimal usage)
- `REDIS_HOST`, `REDIS_PORT`: Redis configuration
- `IGEAR_REQUEST_TIMEOUT`: IGEAR service timeout (default: 180s)
- `CORS_ORIGINS`: Allowed frontend origins

### Data Architecture
The backend uses a **JSON-based data layer** for street and rental statistics:
- **Data File**: `fianzas_wfs_layer.json` (17MB, 9,332 features)
- **Data Source**: Fetched from IGEAR WFS service via `fetch_fianzas_layer.py`
- **Loading**: JSON loaded into memory at startup (~0.7s)
- **Indexes**: Four O(1) hash indexes built automatically:
  - Municipality → Streets
  - (Municipality, Street) → Feature
  - ObjectID → Feature
  - Municipality set (cached)
- **Performance**: Sub-millisecond query times (5-20 microseconds)
- **Memory**: ~18MB per worker (17MB JSON + 1MB indexes)
- **Updates**: Manual refresh via script (data is static, no runtime updates)

## Development Notes

### CORS for Local Development
For local testing, install a CORS browser extension:
- Firefox: [CORS Everywhere](https://addons.mozilla.org/en-US/firefox/addon/cors-everywhere/)

### Geographic Search Types
The application handles three search types with different caching strategies:
- **Postal Codes**: 24-hour cache TTL
- **Municipalities**: 12-hour cache TTL  
- **Streets**: 6-hour cache TTL

### Data Schema
**Primary Data Source**: JSON file with GeoJSON features

Each feature contains:
- `objectid`: Unique identifier
- `via_loc`: Street name and municipality (e.g., "Calle Mayor (Zaragoza)")
- `valores`: JSON array of rental statistics per year and property type
- Geometry: LineString coordinates for street visualization

**Statistics Format** (`valores` field):
```json
[
  {
    "anyo": 2024,
    "tipo": 1,  // 1=Vivienda, 2=Local
    "min": 192.32,
    "max": 300.51,
    "media": 238.40,
    "num": 3
  }
]
```

**Legacy Database** (minimal usage):
- Table: `v_fianzapos_2023` (configurable via `DB_TABLE`)
- Used for: Backward compatibility only
- Modern endpoints use JSON data exclusively

### Testing
- Frontend tests use Jasmine/Karma
- Backend uses pytest (check for test files in `aod-fianzas-back/`)
- E2E tests available via Protractor

## Production Deployment

### Build Commands
- Frontend: `ng build --configuration production --base-href /servicios/alquileres/`
- Backend: Deploy via Docker with proper environment variables
- Nginx serves frontend static files

### Docker Services
- Frontend container: `aod-fianzas-front` (port 4201)
- Backend container: `aod-fianzas-back` (port 4202)
- PostgreSQL: `db-alquileres` (port 5432)
- Redis: `aod-fianzas-redis` (port 6379)

## Code Conventions

### Frontend
- Angular standalone components with TypeScript
- SCSS styling with component-level stylesheets
- RxJS observables for async operations
- OpenLayers integration through `MapService`

### Backend
- FastAPI with Pydantic models for validation
- Service-oriented architecture with clear separation
- Type hints throughout Python code
- Comprehensive error handling for external services

### Shared Patterns
- Feature-based organization in both frontend and backend
- Consistent naming conventions across services
- Environment-based configuration management