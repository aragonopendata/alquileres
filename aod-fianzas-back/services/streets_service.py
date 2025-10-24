import logging
import re
from typing import List, Dict

from services.json_data_service import json_data_service

logger = logging.getLogger(__name__)


class StreetsService:
    """Service for retrieving streets by municipality using JSON data."""

    def __init__(self):
        self.json_service = json_data_service

    def get_streets_by_municipality(
        self,
        municipality: str,
        use_igear: bool = False
    ) -> List[Dict[str, str]]:
        """
        Get streets for a municipality from JSON data.

        Args:
            municipality: Municipality name
            use_igear: Deprecated parameter, kept for backwards compatibility

        Returns:
            List of street dictionaries: [{"nombre_calle": "..."}, ...]
        """
        return self.json_service.get_streets_by_municipality(municipality)


# Global instance
streets_service = StreetsService()
