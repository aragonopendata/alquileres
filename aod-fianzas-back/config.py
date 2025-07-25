from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration settings for the AOD Fianzas backend service."""
    
    # Database settings
    db_url: str = "postgresql://postgres:postgres@db-alquileres/postgres"
    db_table: str = "fianzas_app"
    
    # IGEAR Platform Service URLs
    igear_typed_search_url: str = "https://idearagon.aragon.es/SimpleSearchService/typedSearchService"
    igear_spatial_search_url: str = "https://idearagon.aragon.es/SpatialSearchService/services"
    igear_sita_wms_url: str = "https://idearagon.aragon.es/SITA_WMS"
    igear_visor2d_url: str = "https://idearagon.aragon.es/Visor2D"
    
    # Geographic Configuration
    epsg_code: str = "EPSG:25830"
    aragon_bounding_box: list[tuple[float, float]] = [[571580, 4412223], [812351, 4756639]]
    
    # Search Type Constants
    typed_search_cp: str = "v111_codigo_postal"
    typed_search_direccion: str = "TroidesV"
    typed_search_localidad: str = "Localidad"
    
    # Typename Constants
    typename_cp: str = "carto.v111_codigo_postal"
    typename_direccion: str = "carto.t111_troidesvisor"
    typename_localidad: str = "carto.t112_nucleos"
    
    # WFS Configuration
    wfs_version: str = "1.0.0"
    wfs_output_format: str = "application/json"
    
    # Service Timeout Configuration (increased for slow external APIs)
    igear_request_timeout: int = 120  # seconds (2 minutes for large queries)
    igear_connection_timeout: int = 30  # seconds (connection establishment)
    igear_read_timeout: int = 120  # seconds (reading response data)
    igear_write_timeout: int = 30  # seconds (writing request data)
    
    # Server Configuration
    cors_origins: list[str] = ["http://localhost:4200", "http://localhost:4201", "http://localhost:4202"]
    log_level: str = "INFO"
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    redis_enabled: bool = True
    
    # Cache Configuration
    cache_default_ttl: int = 2592000  # 1 month
    cache_cp_ttl: int = 2592000       # 1 month
    cache_localidad_ttl: int = 2592000  # 1 month
    cache_calle_ttl: int = 2592000     # 1 month
    cache_key_prefix: str = "geo_search"
    cache_version: str = "v1"

    class Config:
        env_file = ".env"
        case_sensitive = False
        # Allow environment variables to override defaults
        env_prefix = ""


# Global settings instance
settings = Settings() 