"""Service for loading and querying fianzas WFS layer data from JSON file."""

import json
import logging
import os
from typing import List, Dict, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


class JsonDataService:
    """Service for accessing fianzas data from JSON file instead of database."""

    def __init__(self, json_file_path: str = None):
        """
        Initialize the JSON data service.

        Args:
            json_file_path: Path to the fianzas_wfs_layer.json file
        """
        if json_file_path is None:
            # Default to file in the same directory as the backend
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            json_file_path = os.path.join(base_dir, "fianzas_wfs_layer.json")

        self.json_file_path = json_file_path
        self._data = None
        self._load_data()

    def _load_data(self):
        """Load JSON data into memory."""
        try:
            logger.info(f"Loading fianzas data from {self.json_file_path}")
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)

            feature_count = len(self._data.get('features', []))
            logger.info(f"Loaded {feature_count} features from JSON file")
        except Exception as e:
            logger.error(f"Error loading JSON file: {e}")
            raise

    @property
    def features(self) -> List[Dict]:
        """Get all features from the JSON data."""
        if self._data is None:
            self._load_data()
        return self._data.get('features', [])

    def _extract_street_and_municipality(self, via_loc: str) -> tuple[Optional[str], Optional[str]]:
        """
        Extract street name and municipality from via_loc field.

        Format: "Calle La Fuente   (Abiego)"
        Returns: ("Calle La Fuente", "Abiego")

        Args:
            via_loc: The via_loc string from feature properties

        Returns:
            Tuple of (street_name, municipality_name)
        """
        if not via_loc:
            return None, None

        # Split by the last occurrence of '('
        if '(' in via_loc and ')' in via_loc:
            last_paren = via_loc.rfind('(')
            street = via_loc[:last_paren].strip()
            municipality = via_loc[last_paren+1:via_loc.rfind(')')].strip()
            return street, municipality

        return via_loc.strip(), None

    def get_municipalities(self) -> List[Dict[str, str]]:
        """
        Get list of unique municipalities.

        Returns:
            List of dicts with format: [{"nombre_municipio": "..."}, ...]
        """
        municipalities = set()

        for feature in self.features:
            via_loc = feature.get('properties', {}).get('via_loc')
            if via_loc:
                _, municipality = self._extract_street_and_municipality(via_loc)
                if municipality:
                    municipalities.add(municipality)

        # Sort and format
        result = [{"nombre_municipio": m} for m in sorted(municipalities)]
        logger.info(f"Found {len(result)} unique municipalities")
        return result

    def get_streets_by_municipality(self, municipality: str) -> List[Dict[str, str]]:
        """
        Get list of streets for a specific municipality.

        Args:
            municipality: Municipality name to filter by

        Returns:
            List of dicts with format: [{"nombre_calle": "..."}, ...]
            Filters out streets with name "-"
        """
        streets = set()

        for feature in self.features:
            via_loc = feature.get('properties', {}).get('via_loc')
            if via_loc:
                street, mun = self._extract_street_and_municipality(via_loc)
                # Case-insensitive comparison and filter out "-" streets
                if mun and street and mun.lower() == municipality.lower() and street != "-":
                    streets.add(street)

        # Sort and format
        result = [{"nombre_calle": s} for s in sorted(streets)]
        logger.info(f"Found {len(result)} streets for municipality '{municipality}'")
        return result

    def get_feature_by_objectid(self, objectid: int) -> Optional[Dict]:
        """
        Get a specific feature by its objectid.

        Args:
            objectid: The objectid to search for

        Returns:
            Feature dict or None if not found
        """
        for feature in self.features:
            if feature.get('properties', {}).get('objectid') == objectid:
                return feature
        return None

    def get_stats_by_street_and_municipality(
        self,
        street: str,
        municipality: str
    ) -> List[Dict]:
        """
        Get rental statistics for a specific street and municipality.

        Args:
            street: Street name
            municipality: Municipality name

        Returns:
            List of stats dicts matching database format:
            [{
                "anyo": 2022,
                "min_renta": 250.0,
                "max_renta": 300.0,
                "media_renta": 275.0,
                "eslocal": "Vivienda",
                "nfianzas": 5
            }, ...]
        """
        # Find the matching feature
        matching_feature = None

        for feature in self.features:
            via_loc = feature.get('properties', {}).get('via_loc')
            if via_loc:
                feat_street, feat_mun = self._extract_street_and_municipality(via_loc)
                # Case-insensitive comparison
                if (feat_street and feat_mun and
                    feat_street.lower() == street.lower() and
                    feat_mun.lower() == municipality.lower()):
                    matching_feature = feature
                    break

        if not matching_feature:
            logger.warning(f"No feature found for street '{street}' in '{municipality}'")
            return []

        # Extract valores (statistics)
        valores = matching_feature.get('properties', {}).get('valores', [])

        # Parse valores if it's a JSON string
        if isinstance(valores, str):
            try:
                valores = json.loads(valores)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse valores JSON for '{street}' in '{municipality}'")
                return []

        # Convert to database format
        stats = []
        for valor in valores:
            # Map tipo to eslocal string
            tipo = valor.get('tipo')
            if tipo == 1:
                eslocal = "Vivienda"
            elif tipo == 2:
                eslocal = "Local"
            else:
                eslocal = "-"

            stat = {
                "anyo": valor.get('anyo'),
                "min_renta": valor.get('min'),
                "max_renta": valor.get('max'),
                "media_renta": valor.get('media'),
                "eslocal": eslocal,
                "nfianzas": valor.get('num')
            }
            stats.append(stat)

        # Sort by year DESC, then by tipo (Vivienda before Local)
        # This matches the database query: ORDER BY anyo DESC, eslocal DESC
        stats.sort(key=lambda x: (-x['anyo'], x['eslocal']), reverse=False)
        stats.sort(key=lambda x: x['anyo'], reverse=True)

        logger.info(f"Found {len(stats)} stats for '{street}' in '{municipality}'")
        return stats


# Global singleton instance
json_data_service = JsonDataService()
