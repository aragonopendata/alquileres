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

        # Index data structures for O(1) lookups
        self._municipality_index: Dict[str, set] = {}  # municipality_lower -> set of street names
        self._street_municipality_index: Dict[tuple, Dict] = {}  # (municipality_lower, street_lower) -> feature
        self._objectid_index: Dict[int, Dict] = {}  # objectid -> feature
        self._municipalities_set: set = set()  # Set of all unique municipality names (original case)
        self._municipalities_cache: Optional[List[Dict[str, str]]] = None  # Cached municipalities list

        self._load_data()
        self._build_indexes()

    def _load_data(self):
        """Load JSON data into memory."""
        try:
            logger.info(f"Loading fianzas data from {self.json_file_path}")
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)

            # Validate data structure
            if 'features' not in self._data:
                logger.error("JSON file missing 'features' key")
                raise ValueError("Invalid JSON structure: missing 'features' key")

            feature_count = len(self._data.get('features', []))
            if feature_count == 0:
                logger.warning("JSON file contains 0 features")

            logger.info(f"Loaded {feature_count} features from JSON file")
        except Exception as e:
            logger.error(f"Error loading JSON file: {e}")
            raise

    def _build_indexes(self):
        """Build lookup indexes for O(1) query performance."""
        logger.info("Building lookup indexes...")

        for feature in self.features:
            properties = feature.get('properties', {})
            via_loc = properties.get('via_loc')
            objectid = properties.get('objectid')

            # Index by objectid
            if objectid is not None:
                self._objectid_index[objectid] = feature

            # Index by street and municipality
            if via_loc:
                street, municipality = self._extract_street_and_municipality(via_loc)

                if municipality:
                    # Store original case municipality
                    self._municipalities_set.add(municipality)

                    municipality_lower = municipality.lower()

                    # Index streets by municipality (filter out "-" streets)
                    if street and street != "-":
                        if municipality_lower not in self._municipality_index:
                            self._municipality_index[municipality_lower] = set()
                        self._municipality_index[municipality_lower].add(street)

                    # Index feature by (municipality, street) combination
                    if street:
                        street_lower = street.lower()
                        key = (municipality_lower, street_lower)
                        self._street_municipality_index[key] = feature

        logger.info(
            f"Indexes built: {len(self._municipalities_set)} municipalities, "
            f"{len(self._street_municipality_index)} street-municipality combinations, "
            f"{len(self._objectid_index)} objectids"
        )

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
        # Return cached result if available
        if self._municipalities_cache is not None:
            return self._municipalities_cache

        # Build result from index (O(1) access to set, O(n log n) sort)
        result = [{"nombre_municipio": m} for m in sorted(self._municipalities_set)]
        logger.info(f"Found {len(result)} unique municipalities")

        # Cache the result
        self._municipalities_cache = result
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
        # O(1) lookup in index
        municipality_lower = municipality.lower()
        streets = self._municipality_index.get(municipality_lower, set())

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
        # O(1) lookup in index
        return self._objectid_index.get(objectid)

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
        # O(1) lookup in index
        key = (municipality.lower(), street.lower())
        matching_feature = self._street_municipality_index.get(key)

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

        # Sort to match database query: ORDER BY anyo DESC, eslocal DESC
        #
        # Explanation:
        # - anyo DESC: Years in descending order (2024, 2023, 2022...)
        # - eslocal DESC: Strings in descending alphabetical order
        #   - 'Vivienda' > 'Local' alphabetically (V > L)
        #   - So DESC puts 'Vivienda' BEFORE 'Local'
        #
        # Python implementation:
        # - reverse=True on tuple (anyo, eslocal) sorts both fields descending
        # - Result: 2024 Vivienda, 2024 Local, 2023 Vivienda, 2023 Local, ...
        #
        # This is CORRECT and matches the database behavior exactly.
        stats.sort(key=lambda x: (x['anyo'], x['eslocal']), reverse=True)

        logger.info(f"Found {len(stats)} stats for '{street}' in '{municipality}'")
        return stats


# Global singleton instance
json_data_service = JsonDataService()
