from pydantic import BaseModel, Field
from typing import List, Optional, Union, Any, Dict
from enum import Enum


class SearchType(str, Enum):
    """Search type enumeration matching frontend TipoBusqueda enum."""
    CP = "CP"
    LOCALIDAD = "LOCALIDAD"
    CALLE = "CALLE"
    SIN_DEFINIR = "SIN_DEFINIR"


class PublicLocationSearchRequest(BaseModel):
    """Public API request model for geographic location search."""
    search_text: str = Field(..., description="Text to search for (postal code, municipality, or street)")
    search_type: Optional[SearchType] = Field(None, description="Explicit search type, auto-detected if not provided")


class LocationSearchRequest(BaseModel):
    """Request model for geographic location search."""
    search_text: str = Field(..., description="Text to search for (postal code, municipality, or street)")
    search_type: Optional[SearchType] = Field(None, description="Explicit search type, auto-detected if not provided")
    layer: str = Field(default="fianzas", description="Map layer to search within")
    distance: int = Field(default=1000, description="Search distance in meters")


class ObjectId(BaseModel):
    """Model representing an IGEAR object identifier."""
    object_id: Optional[str] = Field(None, description="IGEAR object identifier")
    typename: str = Field(..., description="IGEAR typename for the object")


class CRSProperties(BaseModel):
    """Coordinate Reference System properties."""
    name: str


class CRS(BaseModel):
    """Coordinate Reference System definition."""
    type: str
    properties: CRSProperties


class FeatureProperties(BaseModel):
    """Properties of a WFS feature."""
    c_mun_via: Optional[str] = None
    objectid: Optional[int] = None
    valores: Optional[str] = None
    via_loc: Optional[str] = None
    # Allow additional dynamic properties
    class Config:
        extra = "allow"


class Feature(BaseModel):
    """Individual feature in a WFS response."""
    geometry: Optional[Dict[str, Any]] = None
    geometry_name: Optional[str] = None
    id: str
    properties: FeatureProperties
    type: str


class WFSResponse(BaseModel):
    """WFS response model matching frontend structure."""
    crs: CRS
    features: List[Feature]
    total_features: int = Field(alias="totalFeatures", default=0)
    type: str

    class Config:
        allow_population_by_field_name = True
        populate_by_name = True


class LocationSearchResponse(BaseModel):
    """Response model for location search API."""
    success: bool = Field(..., description="Whether the search was successful")
    search_text: str = Field(..., description="Original search text")
    search_type: SearchType = Field(..., description="Detected or specified search type")
    data: Optional[WFSResponse] = Field(None, description="WFS response data if successful")
    message: Optional[str] = Field(None, description="Error message or additional information")


# Models for IGEAR service responses
class SpatialFeature(BaseModel):
    """Feature from spatial search results."""
    id: str
    properties: Dict[str, Any]
    type: str
    geometry: Optional[Dict[str, Any]] = None
    geometry_name: Optional[str] = Field(None, alias="geometry_name")
    
    class Config:
        extra = "allow"


class SpatialFeatureCollection(BaseModel):
    """Feature collection from spatial search."""
    crs: CRS
    features: List[SpatialFeature]
    total_features: Optional[int] = Field(default=0, alias="totalFeatures")
    type: str
    
    class Config:
        allow_population_by_field_name = True
        populate_by_name = True


class SpatialSearchResultado(BaseModel):
    """Individual result from spatial search."""
    capa: str
    distancia: int
    feature_collection: SpatialFeatureCollection = Field(alias="featureCollection")
    
    class Config:
        allow_population_by_field_name = True


class SpatialSearchResults(BaseModel):
    """Complete spatial search response from IGEAR."""
    resultados: List[SpatialSearchResultado]


class HealthStatus(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    services: Dict[str, str] 