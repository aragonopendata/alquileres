"""
Unit tests for StreetsService.

Run with: pytest test_streets_service.py -v
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from lxml import etree

from services.streets_service import StreetsService
from services.geographic_search_service import ServiceUnavailableError
from models import ObjectId, WFSResponse, Feature, FeatureProperties, FeatureCollection, SpatialSearchResults


class TestStreetsService:
    """Test suite for StreetsService."""

    @pytest.fixture
    def streets_service(self):
        """Create a StreetsService instance for testing."""
        return StreetsService()

    @pytest.fixture
    def mock_db_connection(self):
        """Mock database connection."""
        with patch('services.streets_service.connect') as mock_connect:
            yield mock_connect

    def test_get_streets_database_mode(self, streets_service, mock_db_connection):
        """Test database mode returns results."""
        # Mock database results
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("CALLE MAYOR",),
            ("AVENIDA CENTRAL",),
            ("PLAZA DEL PILAR",)
        ]
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        streets = streets_service.get_streets_by_municipality("ZARAGOZA", use_igear=False)

        assert isinstance(streets, list)
        assert len(streets) == 3
        assert all("nombre_calle" in s for s in streets)
        assert streets[0]["nombre_calle"] == "CALLE MAYOR"

    @patch('services.streets_service.cache_service.get')
    def test_get_streets_igear_cache_hit(self, mock_cache_get, streets_service):
        """Test IGEAR mode with cache hit."""
        cached_streets = [
            {"nombre_calle": "CALLE MAYOR"},
            {"nombre_calle": "AVENIDA CENTRAL"}
        ]
        mock_cache_get.return_value = cached_streets

        streets = streets_service.get_streets_by_municipality("ZARAGOZA", use_igear=True)

        assert streets == cached_streets
        mock_cache_get.assert_called_once()

    @patch('services.streets_service.cache_service.set')
    @patch('services.streets_service.cache_service.get')
    def test_get_streets_igear_full_flow(self, mock_cache_get, mock_cache_set, streets_service):
        """Test IGEAR mode with full flow (cache miss)."""
        # Mock cache miss
        mock_cache_get.return_value = None

        # Mock typed search response (XML)
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <List>Test#Municipality#ZARAGOZA#12345#extra</List>
        </Response>"""
        mock_xml = etree.fromstring(xml_content.encode())

        # Mock spatial search results
        mock_spatial_results = Mock()
        mock_resultado = Mock()
        mock_resultado.distancia = 1000
        mock_resultado.capa = "fianzas"
        mock_feature = Mock()
        mock_feature.properties.get.return_value = 999
        mock_resultado.feature_collection.features = [mock_feature]
        mock_spatial_results.resultados = [mock_resultado]

        # Mock WFS response
        mock_wfs_response = Mock(spec=WFSResponse)
        mock_feature1 = Mock()
        mock_feature1.properties.get.return_value = "CALLE MAYOR"
        mock_feature2 = Mock()
        mock_feature2.properties.get.return_value = "AVENIDA CENTRAL"
        mock_feature3 = Mock()
        mock_feature3.properties.get.return_value = "- (ZARAGOZA)"  # Should be filtered
        mock_wfs_response.features = [mock_feature1, mock_feature2, mock_feature3]

        # Patch IGEAR service methods
        with patch.object(streets_service.igear_service, 'typed_search_service', return_value=mock_xml), \
             patch.object(streets_service.igear_service, 'spatial_search_service', return_value=mock_spatial_results), \
             patch.object(streets_service.igear_service, 'sita_wms_get_feature', return_value=mock_wfs_response):

            streets = streets_service.get_streets_by_municipality("ZARAGOZA", use_igear=True)

            # Verify results
            assert isinstance(streets, list)
            assert len(streets) == 2
            assert {"nombre_calle": "AVENIDA CENTRAL"} in streets
            assert {"nombre_calle": "CALLE MAYOR"} in streets
            # Verify filtered street is not in results
            assert {"nombre_calle": "- (ZARAGOZA)"} not in streets

            # Verify cache was set
            mock_cache_set.assert_called_once()

    def test_filter_via_loc_streets(self, streets_service):
        """Test via_loc filtering removes correct patterns."""
        streets = [
            "CALLE MAYOR",
            "- (ZARAGOZA)",
            "AVENIDA CENTRAL",
            "- (HUESCA) NORTE",
            "  - (TEST)",
            "PLAZA DEL PILAR"
        ]
        filtered = streets_service._filter_via_loc_streets(streets)

        assert len(filtered) == 3
        assert "CALLE MAYOR" in filtered
        assert "AVENIDA CENTRAL" in filtered
        assert "PLAZA DEL PILAR" in filtered
        assert "- (ZARAGOZA)" not in filtered
        assert "- (HUESCA) NORTE" not in filtered

    def test_filter_via_loc_streets_empty_list(self, streets_service):
        """Test filtering with empty list."""
        filtered = streets_service._filter_via_loc_streets([])
        assert filtered == []

    def test_extract_street_names(self, streets_service):
        """Test extracting street names from WFS response."""
        # Mock WFS response with features
        mock_feature1 = Mock()
        mock_feature1.properties.get.return_value = "CALLE MAYOR"
        mock_feature2 = Mock()
        mock_feature2.properties.get.return_value = "  AVENIDA CENTRAL  "  # With whitespace
        mock_feature3 = Mock()
        mock_feature3.properties.get.return_value = None  # No via_loc
        mock_feature4 = Mock()
        mock_feature4.properties.get.return_value = ""  # Empty via_loc

        mock_wfs_response = Mock()
        mock_wfs_response.features = [mock_feature1, mock_feature2, mock_feature3, mock_feature4]

        street_names = streets_service._extract_street_names(mock_wfs_response)

        assert len(street_names) == 2
        assert "CALLE MAYOR" in street_names
        assert "AVENIDA CENTRAL" in street_names  # Should be trimmed

    def test_get_object_id_by_municipality_success(self, streets_service):
        """Test successful object ID resolution."""
        # Mock XML response
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <List>Test#Municipality#ZARAGOZA#67890#extra</List>
        </Response>"""
        mock_xml = etree.fromstring(xml_content.encode())

        with patch.object(streets_service.igear_service, 'typed_search_service', return_value=mock_xml):
            object_id = streets_service._get_object_id_by_municipality("ZARAGOZA")

            assert object_id.object_id == "67890"
            assert object_id.typename == "carto.t112_nucleos"

    def test_get_object_id_by_municipality_not_found(self, streets_service):
        """Test object ID resolution when municipality not found."""
        # Mock XML response with no results
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <List></List>
        </Response>"""
        mock_xml = etree.fromstring(xml_content.encode())

        with patch.object(streets_service.igear_service, 'typed_search_service', return_value=mock_xml):
            object_id = streets_service._get_object_id_by_municipality("INVALID_MUNICIPALITY")

            assert object_id.object_id is None

    def test_get_object_id_by_municipality_error(self, streets_service):
        """Test object ID resolution with service error."""
        with patch.object(streets_service.igear_service, 'typed_search_service', side_effect=Exception("Service error")):
            with pytest.raises(ServiceUnavailableError):
                streets_service._get_object_id_by_municipality("ZARAGOZA")

    @patch('services.streets_service.cache_service.get')
    def test_fallback_on_object_id_failure(self, mock_cache_get, streets_service, mock_db_connection):
        """Test fallback to database when object ID resolution fails."""
        # Mock cache miss
        mock_cache_get.return_value = None

        # Mock database results for fallback
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("CALLE FALLBACK",)]
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        # Mock object ID resolution to raise error
        with patch.object(
            streets_service.igear_service,
            'typed_search_service',
            side_effect=Exception("IGEAR unavailable")
        ):
            streets = streets_service.get_streets_by_municipality("ZARAGOZA", use_igear=True)

            # Should fallback to database
            assert isinstance(streets, list)
            assert len(streets) == 1
            assert streets[0]["nombre_calle"] == "CALLE FALLBACK"

    @patch('services.streets_service.cache_service.get')
    def test_fallback_on_empty_object_id(self, mock_cache_get, streets_service, mock_db_connection):
        """Test fallback to database when object ID is None."""
        # Mock cache miss
        mock_cache_get.return_value = None

        # Mock database results for fallback
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("CALLE DATABASE",)]
        mock_db_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        # Mock empty object ID
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <Response><List></List></Response>"""
        mock_xml = etree.fromstring(xml_content.encode())

        with patch.object(streets_service.igear_service, 'typed_search_service', return_value=mock_xml):
            streets = streets_service.get_streets_by_municipality("SMALL_TOWN", use_igear=True)

            # Should fallback to database
            assert isinstance(streets, list)
            assert len(streets) == 1
            assert streets[0]["nombre_calle"] == "CALLE DATABASE"

    def test_build_cql_filter(self, streets_service):
        """Test CQL filter building from spatial results."""
        # Mock spatial results
        mock_spatial_results = Mock()
        mock_resultado = Mock()
        mock_resultado.distancia = 1000
        mock_resultado.capa = "fianzas"

        # Mock features with object IDs
        mock_feature1 = Mock()
        mock_feature1.properties.get.return_value = 111
        mock_feature2 = Mock()
        mock_feature2.properties.get.return_value = 222

        mock_resultado.feature_collection.features = [mock_feature1, mock_feature2]
        mock_spatial_results.resultados = [mock_resultado]

        cql_filter = streets_service._build_cql_filter(mock_spatial_results)

        assert "objectid=111" in cql_filter
        assert "objectid=222" in cql_filter
        assert " OR " in cql_filter

    def test_build_cql_filter_no_results(self, streets_service):
        """Test CQL filter building with no spatial results."""
        mock_spatial_results = Mock()
        mock_spatial_results.resultados = []

        cql_filter = streets_service._build_cql_filter(mock_spatial_results)

        assert cql_filter == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
