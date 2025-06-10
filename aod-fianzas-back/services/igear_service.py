import httpx
import logging
from typing import Optional
from lxml import etree
from config import settings
from models import SpatialSearchResults, WFSResponse

logger = logging.getLogger(__name__)


class IgearService:
    """Service client for IGEAR platform external APIs."""
    
    def __init__(self):
        # Configure timeout with separate values for different operations
        timeout_config = httpx.Timeout(
            connect=settings.igear_connection_timeout,
            read=settings.igear_read_timeout,
            write=settings.igear_write_timeout,
            pool=None  # No timeout for acquiring a connection from the pool
        )
        self.client = httpx.Client(timeout=timeout_config)
        logger.info(f"IGEAR service initialized with timeouts: connect={settings.igear_connection_timeout}s, read={settings.igear_read_timeout}s, write={settings.igear_write_timeout}s")
    
    def __del__(self):
        """Cleanup HTTP client on destruction."""
        if hasattr(self, 'client'):
            self.client.close()
    
    def typed_search_service(self, texto: str, search_type: str, muni: Optional[str] = None) -> etree._Element:
        """
        Call IGEAR typed search service for geographic entity search.
        
        Args:
            texto: Search text
            search_type: Type of search (CP, LOCALIDAD, etc.)
            muni: Optional municipality filter
            
        Returns:
            XML document as lxml Element
            
        Raises:
            httpx.HTTPError: If the request fails
        """
        params = {
            'texto': texto,
            'type': search_type,
            'app': 'DV'
        }
        
        if muni is not None:
            params['muni'] = muni
        
        logger.info(f"Calling typed search service with params: {params}")
        
        try:
            response = self.client.get(
                settings.igear_typed_search_url,
                params=params
            )
            response.raise_for_status()
            
            # Parse XML response
            xml_doc = etree.fromstring(response.content)
            logger.debug(f"Typed search response: {etree.tostring(xml_doc, encoding='unicode')}")
            
            return xml_doc
            
        except httpx.TimeoutException as e:
            logger.error(f"Typed search service timeout after {settings.igear_read_timeout}s: {e}")
            raise
        except httpx.HTTPError as e:
            logger.error(f"Typed search service error: {e}")
            raise
        except etree.XMLSyntaxError as e:
            logger.error(f"XML parsing error: {e}")
            raise
    
    def spatial_search_service(self, object_id: str, typename: str) -> SpatialSearchResults:
        """
        Call IGEAR spatial search service for spatial relationship queries.
        
        Args:
            object_id: IGEAR object identifier
            typename: Object typename
            
        Returns:
            Spatial search results
            
        Raises:
            httpx.HTTPError: If the request fails
        """
        data = {
            'SERVICE': 'DV',
            'TYPENAME': typename,
            'CQL_FILTER': f'OBJECTID={object_id}',
            'PROPERTYNAME': 'OBJECTID',
            'TYPENAME_CONN': 'DV'
        }
        
        logger.info(f"Calling spatial search service with data: {data}")
        
        try:
            response = self.client.post(
                settings.igear_spatial_search_url,
                data=data
            )
            response.raise_for_status()
            
            json_data = response.json()
            logger.debug(f"Spatial search response: {json_data}")
            
            return SpatialSearchResults(**json_data)
            
        except httpx.TimeoutException as e:
            logger.error(f"Spatial search service timeout after {settings.igear_read_timeout}s: {e}")
            raise
        except httpx.HTTPError as e:
            logger.error(f"Spatial search service error: {e}")
            raise
        except Exception as e:
            logger.error(f"Spatial search parsing error: {e}")
            raise
    
    def sita_wms_get_feature(self, typename: str, cql_filter: str) -> WFSResponse:
        """
        Call IGEAR SITA WMS service for WFS feature retrieval.
        
        Args:
            typename: Feature typename
            cql_filter: CQL filter expression
            
        Returns:
            WFS response with features
            
        Raises:
            httpx.HTTPError: If the request fails
        """
        data = {
            'service': 'WFS',
            'version': settings.wfs_version,
            'request': 'GetFeature',
            'typename': typename,
            'outputFormat': settings.wfs_output_format,
            'srsname': settings.epsg_code,
            'CQL_FILTER': cql_filter
        }
        
        logger.info(f"Calling SITA WMS service with data: {data}")
        
        try:
            response = self.client.post(
                settings.igear_sita_wms_url,
                data=data
            )
            response.raise_for_status()
            
            json_data = response.json()
            logger.debug(f"SITA WMS response: {json_data}")
            
            return WFSResponse(**json_data)
            
        except httpx.TimeoutException as e:
            logger.error(f"SITA WMS service timeout after {settings.igear_read_timeout}s: {e}")
            raise
        except httpx.HTTPError as e:
            logger.error(f"SITA WMS service error: {e}")
            raise
        except Exception as e:
            logger.error(f"SITA WMS parsing error: {e}")
            raise
    
    def visor2d_service(self, typename: str, cql_filter: str) -> WFSResponse:
        """
        Call IGEAR Visor2D service for 2D visualization data.
        
        Args:
            typename: Feature typename
            cql_filter: CQL filter expression
            
        Returns:
            WFS response with features
            
        Raises:
            httpx.HTTPError: If the request fails
        """
        data = {
            'service': 'WFS',
            'version': settings.wfs_version,
            'request': 'GetFeature',
            'typename': typename,
            'outputFormat': settings.wfs_output_format,
            'srsname': settings.epsg_code,
            'CQL_FILTER': cql_filter
        }
        
        logger.info(f"Calling Visor2D service with data: {data}")
        
        try:
            response = self.client.post(
                settings.igear_visor2d_url,
                data=data
            )
            response.raise_for_status()
            
            json_data = response.json()
            logger.debug(f"Visor2D response: {json_data}")
            
            return WFSResponse(**json_data)
            
        except httpx.TimeoutException as e:
            logger.error(f"Visor2D service timeout after {settings.igear_read_timeout}s: {e}")
            raise
        except httpx.HTTPError as e:
            logger.error(f"Visor2D service error: {e}")
            raise
        except Exception as e:
            logger.error(f"Visor2D parsing error: {e}")
            raise 