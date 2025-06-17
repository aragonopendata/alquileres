import logging
import re
from typing import Optional

import httpx

from config import settings
from models import (
    LocationSearchRequest, LocationSearchResponse, SearchType,
    ObjectId, WFSResponse
)
from services.cache_service import cache_service
from services.igear_service import IgearService

logger = logging.getLogger(__name__)


class ServiceTimeoutError(Exception):
    """Exception raised when external service calls timeout."""
    pass


class ServiceUnavailableError(Exception):
    """Exception raised when external services are unavailable."""
    pass


class GeographicSearchService:
    """Service for consolidated geographic search operations."""
    
    def __init__(self):
        self.igear_service = IgearService()
    
    def search_location(self, request: LocationSearchRequest) -> LocationSearchResponse:
        """
        Main method to search for a location and return WFS features.
        Implements cache-first lookup strategy.
        
        Args:
            request: Location search request
            
        Returns:
            Location search response with WFS data or error message
        """
        try:
            # Detect search type if not provided
            search_type = request.search_type or self._detect_search_type(request.search_text)
            logger.info(f"Searching for '{request.search_text}' with type '{search_type}'")
            
            # Try cache first
            cache_key = self._generate_cache_key(request, search_type)
            cached_result = self._get_cached_result(cache_key, request.search_text)
            if cached_result:
                return cached_result
            
            # Cache miss - perform actual search
            logger.info(f"Cache MISS for search: {request.search_text}")
            return self._perform_search(request, search_type, cache_key)
            
        except Exception as e:
            logger.error(f"Error in location search: {e}")
            return self._create_error_response(
                request.search_text,
                search_type or SearchType.SIN_DEFINIR,
                f"Ha habido un fallo en la consulta: {str(e)}"
            )
    
    def _generate_cache_key(self, request: LocationSearchRequest, search_type: SearchType) -> str:
        """Generate cache key for the search request."""
        return cache_service.get_cache_key(
            search_type.value.lower(), 
            f"{request.search_text}_{request.layer}_{request.distance}"
        )
    
    def _get_cached_result(self, cache_key: str, search_text: str) -> Optional[LocationSearchResponse]:
        """Try to get cached result for the search."""
        cached_result = cache_service.get(cache_key)
        if cached_result:
            logger.info(f"Cache HIT for search: {search_text}")
            return LocationSearchResponse(**cached_result)
        return None
    
    def _perform_search(self, request: LocationSearchRequest, search_type: SearchType, cache_key: str) -> LocationSearchResponse:
        """Perform the actual search operation."""
        # Resolve object ID
        object_id_result = self._resolve_object_id_with_error_handling(request.search_text, search_type)
        if isinstance(object_id_result, LocationSearchResponse):
            # Error occurred during object ID resolution
            return object_id_result
        
        object_id = object_id_result
        if not object_id.object_id:
            return self._handle_object_id_not_found(request.search_text, search_type, cache_key)
        
        # Get WFS features
        return self._get_wfs_features_with_error_handling(
            object_id, request, search_type, cache_key
        )
    
    def _resolve_object_id_with_error_handling(self, search_text: str, search_type: SearchType) -> ObjectId | LocationSearchResponse:
        """Resolve object ID with proper error handling for service issues."""
        try:
            return self._resolve_object_id(search_text, search_type)
        except (ServiceTimeoutError, ServiceUnavailableError) as service_error:
            logger.warning(f"External service error during object ID resolution for '{search_text}': {service_error}")
            return self._create_service_unavailable_response(search_text, search_type)
    
    def _handle_object_id_not_found(self, search_text: str, search_type: SearchType, cache_key: str) -> LocationSearchResponse:
        """Handle case when object ID is not found."""
        error_response = self._create_error_response(
            search_text,
            search_type,
            f"No se han encontrado resultados para la búsqueda {search_text}. Por favor, revise su consulta."
        )
        
        # Cache legitimate "not found" responses for a shorter time (5 minutes)
        if cache_service.should_cache_error(error_response.message):
            cache_service.set(cache_key, error_response.model_dump(), 300)
        
        return error_response
    
    def _get_wfs_features_with_error_handling(
        self, 
        object_id: ObjectId, 
        request: LocationSearchRequest, 
        search_type: SearchType, 
        cache_key: str
    ) -> LocationSearchResponse:
        """Get WFS features with proper error handling."""
        try:
            wfs_response = self._get_wfs_features(
                object_id.object_id,
                object_id.typename,
                request.layer,
                request.distance
            )
            
            return self._create_success_response_and_cache(
                request.search_text, search_type, wfs_response, cache_key
            )
            
        except (ServiceTimeoutError, ServiceUnavailableError) as service_error:
            logger.warning(f"External service error for search '{request.search_text}': {service_error}")
            return self._create_service_unavailable_response(request.search_text, search_type)
    
    def _create_success_response_and_cache(
        self, 
        search_text: str, 
        search_type: SearchType, 
        wfs_response: WFSResponse, 
        cache_key: str
    ) -> LocationSearchResponse:
        """Create success response and cache it."""
        success_response = LocationSearchResponse(
            success=True,
            search_text=search_text,
            search_type=search_type,
            data=wfs_response,
            message="Búsqueda completada exitosamente"
        )
        
        # Cache successful response with appropriate TTL
        ttl = cache_service.get_ttl_for_search_type(search_type.value.lower())
        cache_service.set(cache_key, success_response.model_dump(), ttl)
        
        return success_response
    
    def _create_error_response(self, search_text: str, search_type: SearchType, message: str) -> LocationSearchResponse:
        """Create error response."""
        return LocationSearchResponse(
            success=False,
            search_text=search_text,
            search_type=search_type,
            message=message
        )
    
    def _create_service_unavailable_response(self, search_text: str, search_type: SearchType) -> LocationSearchResponse:
        """Create service unavailable response."""
        return self._create_error_response(
            search_text,
            search_type,
            "Los servicios externos están temporalmente no disponibles. Por favor, inténtelo de nuevo más tarde."
        )
    
    def _detect_search_type(self, search_string: str) -> SearchType:
        """
        Detect search type using regex patterns matching frontend logic.
        
        Args:
            search_string: Input search text
            
        Returns:
            Detected search type
        """
        # Spanish postal code pattern (5 digits, first two digits 01-52)
        cp_regex = re.compile(r'^(?:0?[1-9]|[1-4]\d|5[0-2])\d{3}$')
        
        # Street address pattern (text, comma, text without digits)
        calle_regex = re.compile(r'^[\w\s]+,[^\d]+?$')
        
        # Municipality pattern (text without digits or commas)
        localidad_regex = re.compile(r'^[^\d,]+$')
        
        search_string = search_string.strip()
        
        if cp_regex.match(search_string):
            logger.debug(f"Detected search type: CP for '{search_string}'")
            return SearchType.CP
        elif calle_regex.match(search_string):
            fields = search_string.split(',')
            if len(fields) == 2 and fields[1].strip():
                logger.debug(f"Detected search type: CALLE for '{search_string}'")
                return SearchType.CALLE
        elif localidad_regex.match(search_string) and search_string:
            logger.debug(f"Detected search type: LOCALIDAD for '{search_string}'")
            return SearchType.LOCALIDAD
        
        logger.debug(f"Could not detect search type for '{search_string}', using SIN_DEFINIR")
        return SearchType.SIN_DEFINIR
    
    def _resolve_object_id(self, search_text: str, search_type: SearchType) -> ObjectId:
        """
        Resolve IGEAR object ID based on search text and type.
        
        Args:
            search_text: Search text
            search_type: Type of search
            
        Returns:
            Object ID with typename
        """
        if search_type == SearchType.CP:
            return self._get_object_id_by_cp(search_text)
        elif search_type == SearchType.LOCALIDAD:
            return self._get_object_id_by_localidad(search_text)
        elif search_type == SearchType.CALLE:
            # For street addresses, split by comma
            fields = search_text.split(',')
            if len(fields) >= 2:
                street = fields[0].strip()
                municipality = fields[1].strip()
                return self._get_object_id_by_direccion(street, municipality)
        
        # Return empty object ID for unsupported search types
        return ObjectId(object_id=None, typename="")
    
    def _get_object_id_by_cp(self, postal_code: str) -> ObjectId:
        """
        Get object ID for postal code search.
        
        Args:
            postal_code: Postal code to search
            
        Returns:
            Object ID for the postal code
        """
        try:
            xml_response = self.igear_service.typed_search_service(
                postal_code, 
                settings.typed_search_cp
            )
            
            # Extract object ID from XML response
            list_elements = xml_response.xpath('//List')
            if list_elements and list_elements[0].text:
                parts = list_elements[0].text.split('#')
                if len(parts) > 3:
                    object_id = parts[3]
                    return ObjectId(
                        object_id=object_id,
                        typename=settings.typename_cp
                    )
            
            return ObjectId(object_id=None, typename=settings.typename_cp)
            
        except httpx.TimeoutException as e:
            logger.error(f"Service timeout getting object ID by CP after {settings.igear_read_timeout}s: {e}")
            raise ServiceTimeoutError(f"External service timeout during postal code search after {settings.igear_read_timeout} seconds: {e}")
        except Exception as e:
            error_msg = str(e).lower()
            if any(timeout_keyword in error_msg for timeout_keyword in ['timeout', 'timed out', 'read timeout']):
                logger.error(f"Service timeout getting object ID by CP: {e}")
                raise ServiceTimeoutError(f"External service timeout during postal code search: {e}")
            elif any(conn_keyword in error_msg for conn_keyword in ['connection', 'connect', 'network', 'unreachable']):
                logger.error(f"Service unavailable getting object ID by CP: {e}")
                raise ServiceUnavailableError(f"External service unavailable during postal code search: {e}")
            else:
                logger.error(f"Error getting object ID by CP: {e}")
                return ObjectId(object_id=None, typename=settings.typename_cp)
    
    def _get_object_id_by_localidad(self, municipality: str) -> ObjectId:
        """
        Get object ID for municipality search.
        
        Args:
            municipality: Municipality name to search
            
        Returns:
            Object ID for the municipality
        """
        try:
            xml_response = self.igear_service.typed_search_service(
                municipality,
                settings.typed_search_localidad
            )
            
            # Extract object ID from XML response
            list_elements = xml_response.xpath('//List')
            if list_elements and list_elements[0].text:
                parts = list_elements[0].text.split('#')
                if len(parts) > 3:
                    object_id = parts[3]
                    return ObjectId(
                        object_id=object_id,
                        typename=settings.typename_localidad
                    )
            
            return ObjectId(object_id=None, typename=settings.typename_localidad)
            
        except httpx.TimeoutException as e:
            logger.error(f"Service timeout getting object ID by localidad after {settings.igear_read_timeout}s: {e}")
            raise ServiceTimeoutError(f"External service timeout during municipality search after {settings.igear_read_timeout} seconds: {e}")
        except Exception as e:
            error_msg = str(e).lower()
            if any(timeout_keyword in error_msg for timeout_keyword in ['timeout', 'timed out', 'read timeout']):
                logger.error(f"Service timeout getting object ID by localidad: {e}")
                raise ServiceTimeoutError(f"External service timeout during municipality search: {e}")
            elif any(conn_keyword in error_msg for conn_keyword in ['connection', 'connect', 'network', 'unreachable']):
                logger.error(f"Service unavailable getting object ID by localidad: {e}")
                raise ServiceUnavailableError(f"External service unavailable during municipality search: {e}")
            else:
                logger.error(f"Error getting object ID by localidad: {e}")
                return ObjectId(object_id=None, typename=settings.typename_localidad)
    
    def _get_object_id_by_direccion(self, street: str, municipality: str) -> ObjectId:
        """
        Get object ID for street address search.
        
        Args:
            street: Street name
            municipality: Municipality name
            
        Returns:
            Object ID for the street address
        """
        try:
            # First, get the c_mun_via from typed search
            xml_response = self.igear_service.typed_search_service(
                street,
                settings.typed_search_direccion,
                municipality
            )
            
            list_elements = xml_response.xpath('//List')
            if not list_elements or not list_elements[0].text:
                return ObjectId(object_id=None, typename=settings.typename_direccion)
            
            parts = list_elements[0].text.split('#')
            if len(parts) <= 3:
                return ObjectId(object_id=None, typename=settings.typename_direccion)
            
            c_mun_via = parts[3]
            cql_filter = f"c_mun_via='{c_mun_via}'"
            
            # Then, get the actual object ID from visor2D service
            wfs_response = self.igear_service.visor2d_service(
                settings.typed_search_direccion,
                cql_filter
            )
            
            if wfs_response.features and len(wfs_response.features) > 0:
                object_id = wfs_response.features[0].properties.objectid
                return ObjectId(
                    object_id=str(object_id) if object_id else None,
                    typename=settings.typename_direccion
                )
            
            return ObjectId(object_id=None, typename=settings.typename_direccion)
            
        except Exception as e:
            logger.error(f"Error getting object ID by direccion: {e}")
            return ObjectId(object_id=None, typename=settings.typename_direccion)
    
    def _get_wfs_features(self, object_id: str, typename: str, layer: str, distance: int) -> WFSResponse:
        """
        Get WFS features for a given object ID and parameters.
        
        Args:
            object_id: IGEAR object identifier
            typename: Object typename
            layer: Map layer to search
            distance: Search distance in meters
            
        Returns:
            WFS response with features (fitered features with via_loc like '- (*)')
            
        Raises:
            ServiceTimeoutError: When external service calls timeout
            ServiceUnavailableError: When external services are unavailable
        """
        try:
            # Get spatial search results
            spatial_results = self.igear_service.spatial_search_service(object_id, typename)
            
            # Build CQL filter based on spatial results
            cql_filter = ""
            
            # For postal codes, include the original object ID
            if typename == settings.typename_cp:
                cql_filter = f"objectid={object_id}"
            
            # Process spatial search results to build filter
            for resultado in spatial_results.resultados:
                if resultado.distancia == distance and layer in resultado.capa:
                    for feature in resultado.feature_collection.features:
                        feature_oid = feature.properties.get('objectid')
                        if feature_oid:
                            if cql_filter:
                                cql_filter += f" OR objectid={feature_oid}"
                            else:
                                cql_filter = f"objectid={feature_oid}"
                    break
            
            if not cql_filter:
                logger.warning(f"No CQL filter generated for object_id={object_id}, layer={layer}, distance={distance}")
                # Return empty WFS response - this is legitimate (no features found)
                return WFSResponse(
                    crs={"type": "name", "properties": {"name": settings.epsg_code}},
                    features=[],
                    total_features=0,
                    type="FeatureCollection"
                )
            
            # Get WFS features using the CQL filter
            wfs_response = self.igear_service.sita_wms_get_feature(layer, cql_filter)
            
            # Filter out features with via_loc starting with '- (*)'
            original_count = len(wfs_response.features)
            filtered_response = self._filter_via_loc_features(wfs_response)
            filtered_count = len(filtered_response.features)
            
            logger.info(f"Retrieved {original_count} features, filtered to {filtered_count} features for search")
            return filtered_response
            
        except httpx.TimeoutException as e:
            logger.error(f"Service timeout getting WFS features after {settings.igear_read_timeout}s: {e}")
            raise ServiceTimeoutError(f"External service timeout after {settings.igear_read_timeout} seconds: {e}")
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check for timeout-related errors (fallback for other timeout types)
            if any(timeout_keyword in error_msg for timeout_keyword in ['timeout', 'timed out', 'read timeout']):
                logger.error(f"Service timeout getting WFS features: {e}")
                raise ServiceTimeoutError(f"External service timeout: {e}")
            
            # Check for connection-related errors
            if any(conn_keyword in error_msg for conn_keyword in ['connection', 'connect', 'network', 'unreachable']):
                logger.error(f"Service unavailable getting WFS features: {e}")
                raise ServiceUnavailableError(f"External service unavailable: {e}")
            
            # For other errors, still raise as service error
            logger.error(f"Service error getting WFS features: {e}")
            raise ServiceUnavailableError(f"External service error: {e}")
    
    def _filter_via_loc_features(self, wfs_response: WFSResponse) -> WFSResponse:
        """
        Filter out features with via_loc starting with '- (*)' pattern.
        
        Args:
            wfs_response: Original WFS response
            
        Returns:
            Filtered WFS response with features removed
        """
        if not wfs_response.features:
            return wfs_response
        
        # Pattern to match via_loc starting with optional spaces, dash, spaces, and parentheses
        pattern = re.compile(r'^\s*-\s*\([^)]*\)')
        
        filtered_features = []
        filtered_via_locs = []
        
        for feature in wfs_response.features:
            via_loc = feature.properties.via_loc
            
            # Keep feature if via_loc is None, empty, or doesn't match the pattern
            if not via_loc or not pattern.match(via_loc):
                filtered_features.append(feature)
            else:
                # Log the filtered via_loc for debugging
                filtered_via_locs.append(via_loc)
        
        # Debug log showing filtered features
        if filtered_via_locs:
            logger.debug(f"Filtered out features with via_loc: {filtered_via_locs}")
        
        # Return new WFS response with filtered features
        return WFSResponse(
            crs=wfs_response.crs,
            features=filtered_features,
            total_features=len(filtered_features),
            type=wfs_response.type
        )