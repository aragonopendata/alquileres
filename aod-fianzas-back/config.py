from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional


class Settings(BaseSettings):
    """Configuration settings for the AOD Fianzas backend service."""

    # Environment Configuration
    # Options: local (localhost), des (desarrollo), pre (preproduction), pro (production)
    environment: str = "local"
    cors_origins_override: Optional[str] = None  # Comma-separated CORS origins (overrides environment defaults)

    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate that environment is one of the allowed values."""
        allowed = ['local', 'des', 'pre', 'pro']
        if v not in allowed:
            raise ValueError(f'environment must be one of {allowed}, got: {v}')
        return v

    def get_igear_domain(self) -> str:
        """
        Returns IGEAR domain based on environment.

        Environment mappings:
        - local: idearagon.aragon.es (production, no VPN required)
        - des: idearagondes.aragon.es (desarrollo, requires VPN)
        - pre: idearagon.aragon.es (preproduction, no VPN required)
        - pro: idearagon.aragon.es (production)

        Returns:
            IGEAR domain hostname for the current environment
        """
        if self.environment == "des":
            return "idearagondes.aragon.es"
        else:  # local, pre, and pro all use production IGEAR
            return "idearagon.aragon.es"

    def get_cors_origins_list(self) -> list[str]:
        """
        Returns CORS origins based on environment or override.

        Returns:
            List of allowed CORS origins for the current environment
        """
        # Use override if provided
        if self.cors_origins_override:
            return [origin.strip() for origin in self.cors_origins_override.split(",")]

        # Default origins based on environment
        if self.environment == "local":
            return [
                "http://localhost:4200",
                "http://localhost:4201",
                "http://localhost:4202"
            ]
        elif self.environment == "des":
            return ["https://desopendata.aragon.es"]
        elif self.environment == "pre":
            return ["https://preopendata.aragon.es"]
        else:  # pro
            return ["https://opendata.aragon.es"]

    @property
    def igear_typed_search_url(self) -> str:
        """TypedSearch service URL for the current environment."""
        return f"https://{self.get_igear_domain()}/SimpleSearchService/typedSearchService"

    @property
    def igear_spatial_search_url(self) -> str:
        """SpatialSearch service URL for the current environment."""
        return f"https://{self.get_igear_domain()}/SpatialSearchService/services"

    @property
    def igear_sita_wms_url(self) -> str:
        """SITA WMS service URL for the current environment."""
        return f"https://{self.get_igear_domain()}/SITA_WMS"

    @property
    def igear_visor2d_url(self) -> str:
        """Visor2D service URL for the current environment."""
        return f"https://{self.get_igear_domain()}/Visor2D"

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