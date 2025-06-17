# AOD Fianzas Backend API

FastAPI backend service for Aragon rental deposit data with geographic search capabilities.

## Features

- **Geographic Search**: Unified search endpoint for postal codes, municipalities, and streets
- **IGEAR Integration**: Connects to Aragon's geographic information services
- **Redis Caching**: Configurable caching layer for improved performance
- **Database Integration**: PostgreSQL connection for rental deposit statistics
- **Health Monitoring**: Health check endpoints for service monitoring

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
- `DB_URL` - PostgreSQL connection string
- `REDIS_HOST` - Redis server host
- `REDIS_PORT` - Redis server port
- `CORS_ORIGINS` - Allowed CORS origins
- `LOG_LEVEL` - Logging level

## Dependencies

- FastAPI - Web framework
- PostgreSQL - Database (psycopg2)
- Redis - Caching layer
- HTTPX - HTTP client for IGEAR services
- Pydantic - Data validation

## Architecture

The application follows a service-oriented architecture:
- **Services**: Geographic search, cache management, IGEAR integration
- **Models**: Pydantic models for request/response validation
- **Database**: PostgreSQL queries for rental statistics
- **External APIs**: Integration with Aragon's IGEAR platform
