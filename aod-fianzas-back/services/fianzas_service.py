"""
Service for fetching rental (fianzas) data from IGEAR services.
Replaces direct database queries with IGEAR API calls.
"""
import json
import logging
from typing import List, Dict, Optional

from config import settings
from services.igear_service import IgearService

logger = logging.getLogger(__name__)


class FianzasService:
    """Service for retrieving rental deposit data from IGEAR services."""

    def __init__(self):
        self.igear_service = IgearService()

    def get_streets_by_municipality(self, municipality: str) -> List[Dict[str, str]]:
        """
        Get list of streets for a municipality from IGEAR services.

        Args:
            municipality: Municipality name

        Returns:
            List of street dictionaries with 'nombre_calle' key
        """
        try:
            logger.info(f"Fetching streets for municipality: {municipality}")

            # Step 1: Get municipality object ID
            object_id = self._get_municipality_object_id(municipality)
            if not object_id:
                logger.warning(f"Municipality not found: {municipality}")
                return []

            # Step 2: Get spatial search results for fianzas layer
            spatial_results = self.igear_service.spatial_search_service(
                object_id,
                settings.typename_localidad
            )

            # Step 3: Find fianzas layer at distance=1000
            fianzas_layer = self._find_fianzas_layer(spatial_results, distance=1000)
            if not fianzas_layer:
                logger.warning(f"No fianzas data found for municipality: {municipality}")
                return []

            # Step 4: Get WFS features
            cql_filter = self._build_cql_filter_from_features(
                fianzas_layer.feature_collection.features
            )
            if not cql_filter:
                logger.warning(f"No features to query for municipality: {municipality}")
                return []

            wfs_response = self.igear_service.sita_wms_get_feature(
                typename="fianzas",
                cql_filter=cql_filter
            )

            # Step 5: Extract unique street names
            streets = self._extract_unique_streets(wfs_response.features, municipality)

            logger.info(f"Found {len(streets)} streets for municipality: {municipality}")
            return streets

        except Exception as e:
            logger.error(f"Error fetching streets for {municipality}: {e}")
            raise

    def get_stats_by_street_and_municipality(
        self,
        street: str,
        municipality: str
    ) -> List[Dict]:
        """
        Get rental statistics for a specific street and municipality from IGEAR services.

        Args:
            street: Street name
            municipality: Municipality name

        Returns:
            List of statistics dictionaries matching current API format:
            - anyo: year
            - min_renta: minimum rent
            - max_renta: maximum rent
            - media_renta: average rent
            - eslocal: "Vivienda" or "Local"
            - nfianzas: number of deposits
        """
        try:
            logger.info(f"Fetching stats for street '{street}' in '{municipality}'")

            # Step 1: Search for the street using typed search
            xml_response = self.igear_service.typed_search_service(
                texto=street,
                search_type=settings.typed_search_direccion,
                muni=municipality
            )

            # Step 2: Extract c_mun_via from the first result
            list_elements = xml_response.xpath('//List')
            if not list_elements or not list_elements[0].text:
                logger.warning(f"Street not found: {street} in {municipality}")
                return []

            parts = list_elements[0].text.split('#')
            if len(parts) <= 3:
                logger.warning(f"Invalid response format for street: {street}")
                return []

            c_mun_via = parts[3]
            logger.debug(f"Found c_mun_via: {c_mun_via}")

            # Step 3: Get feature from visor2d to get objectid
            cql_filter = f"c_mun_via='{c_mun_via}'"
            visor_response = self.igear_service.visor2d_service(
                typename=settings.typed_search_direccion,
                cql_filter=cql_filter
            )

            if not visor_response.features:
                logger.warning(f"No features found for c_mun_via: {c_mun_via}")
                return []

            street_objectid = str(visor_response.features[0].properties.objectid)
            logger.debug(f"Found street objectid: {street_objectid}")

            # Step 4: Get spatial search results for fianzas
            spatial_results = self.igear_service.spatial_search_service(
                street_objectid,
                settings.typename_direccion
            )

            # Step 5: Find fianzas layer at distance=1000
            fianzas_layer = self._find_fianzas_layer(spatial_results, distance=1000)
            if not fianzas_layer:
                logger.warning(f"No fianzas data found for street: {street}")
                return []

            # Step 6: Build CQL filter and get WFS features
            cql_filter = self._build_cql_filter_from_features(
                fianzas_layer.feature_collection.features
            )
            if not cql_filter:
                logger.warning(f"No features in fianzas layer for street: {street}")
                return []

            wfs_response = self.igear_service.sita_wms_get_feature(
                typename="fianzas",
                cql_filter=cql_filter
            )

            # Step 7: Find the matching feature and parse valores
            # Try to match by c_mun_via first, then fall back to street name matching
            stats = self._extract_stats_from_features(
                wfs_response.features,
                c_mun_via,
                street,
                municipality,
                fallback_to_name_match=True
            )

            logger.info(f"Found {len(stats)} stat records for '{street}' in '{municipality}'")
            return stats

        except Exception as e:
            logger.error(f"Error fetching stats for '{street}' in '{municipality}': {e}")
            raise

    def _get_municipality_object_id(self, municipality: str) -> Optional[str]:
        """Get IGEAR object ID for a municipality."""
        try:
            xml_response = self.igear_service.typed_search_service(
                texto=municipality,
                search_type=settings.typed_search_localidad
            )

            list_elements = xml_response.xpath('//List')
            if list_elements and list_elements[0].text:
                parts = list_elements[0].text.split('#')
                if len(parts) > 3:
                    return parts[3]

            return None
        except Exception as e:
            logger.error(f"Error getting municipality object ID: {e}")
            return None

    def _find_fianzas_layer(self, spatial_results, distance: int):
        """Find the fianzas layer in spatial search results."""
        for resultado in spatial_results.resultados:
            if 'fianzas' in resultado.capa.lower() and resultado.distancia == distance:
                return resultado
        return None

    def _build_cql_filter_from_features(self, features: List) -> str:
        """Build CQL filter from spatial search features."""
        cql_filter = ""
        for feature in features:
            feature_oid = feature.properties.get('objectid')
            if feature_oid:
                if cql_filter:
                    cql_filter += f" OR objectid={feature_oid}"
                else:
                    cql_filter = f"objectid={feature_oid}"
        return cql_filter

    def _extract_unique_streets(
        self,
        features: List,
        municipality: str
    ) -> List[Dict[str, str]]:
        """Extract unique street names from WFS features."""
        street_names = set()

        for feature in features:
            via_loc = feature.properties.via_loc
            if via_loc:
                # via_loc format: "Calle San Antonio de Padua   (Zaragoza)"
                # Extract street name (everything before the municipality in parentheses)
                if '(' in via_loc:
                    street_name = via_loc.split('(')[0].strip()
                else:
                    street_name = via_loc.strip()

                street_names.add(street_name)

        # Convert to list of dicts matching current API format
        streets = [
            {"nombre_calle": street_name}
            for street_name in sorted(street_names)
        ]

        return streets

    def _extract_stats_from_features(
        self,
        features: List,
        c_mun_via: str,
        street: str,
        municipality: str,
        fallback_to_name_match: bool = False
    ) -> List[Dict]:
        """Extract and parse statistics from WFS features."""
        # Find the feature that matches our c_mun_via
        target_feature = None
        for feature in features:
            if feature.properties.c_mun_via == c_mun_via:
                target_feature = feature
                break

        # If not found by c_mun_via, try matching by street name in via_loc
        if not target_feature and fallback_to_name_match:
            logger.debug(f"No exact match for c_mun_via: {c_mun_via}, trying name match")
            # Normalize street name for comparison
            normalized_search = street.lower().strip()

            for feature in features:
                if feature.properties.via_loc:
                    # Extract street name from via_loc: "Calle XXX (Municipality)"
                    via_loc_lower = feature.properties.via_loc.lower()

                    # Check if the search street name is in the via_loc
                    if normalized_search in via_loc_lower and municipality.lower() in via_loc_lower:
                        target_feature = feature
                        logger.debug(f"Found match by name: {feature.properties.via_loc}")
                        break

        if not target_feature:
            logger.warning(f"No feature found for street: {street} (c_mun_via: {c_mun_via})")
            return []

        # Parse the valores JSON field
        valores_str = target_feature.properties.valores
        if not valores_str:
            logger.warning(f"No valores data for c_mun_via: {c_mun_via}")
            return []

        try:
            valores_data = json.loads(valores_str)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing valores JSON: {e}")
            return []

        # Transform to match current API format
        stats = []
        for valor in valores_data:
            # Filter out entries from year 2000 or earlier (matching DB query)
            if valor.get('anyo', 0) <= 2000:
                continue

            stat = {
                "anyo": valor.get('anyo'),
                "min_renta": valor.get('min'),
                "max_renta": valor.get('max'),
                "media_renta": valor.get('media'),
                "eslocal": self._get_eslocal(valor.get('tipo')),
                "nfianzas": valor.get('num')
            }
            stats.append(stat)

        # Sort by year descending, then by tipo descending (matching DB query)
        # tipo: 1=Vivienda, 2=Local, so we reverse to get Local first
        stats.sort(
            key=lambda x: (-(x['anyo'] or 0), -self._get_tipo_value(x['eslocal']))
        )

        return stats

    @staticmethod
    def _get_eslocal(tipo: int) -> str:
        """Convert tipo code to eslocal string."""
        if tipo == 1:
            return "Vivienda"
        elif tipo == 2:
            return "Local"
        else:
            return "-"

    @staticmethod
    def _get_tipo_value(eslocal: str) -> int:
        """Convert eslocal string back to tipo value for sorting."""
        if eslocal == "Vivienda":
            return 1
        elif eslocal == "Local":
            return 2
        else:
            return 0


# Create singleton instance
fianzas_service = FianzasService()
