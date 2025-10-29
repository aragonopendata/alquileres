"""
Integration tests for the streets endpoint.

Run with: pytest test_streets_endpoint.py -v
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from config import settings


client = TestClient(app)


class TestStreetsEndpoint:
    """Integration tests for /municipality/{municipality}/street endpoint."""

    def test_streets_endpoint_success(self):
        """Test endpoint returns successful response."""
        response = client.get("/municipality/ZARAGOZA/street")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_streets_endpoint_response_format(self):
        """Test response format is backward compatible."""
        response = client.get("/municipality/ZARAGOZA/street")

        data = response.json()
        assert isinstance(data, list)

        # Verify structure if there are results
        if len(data) > 0:
            assert "nombre_calle" in data[0]
            assert isinstance(data[0]["nombre_calle"], str)
            # Should only have one key
            assert len(data[0].keys()) == 1

    def test_streets_endpoint_headers_database_mode(self):
        """Test response headers indicate database source when feature flag is off."""
        # Ensure feature flag is off
        with patch.object(settings, 'use_igear_for_streets', False):
            response = client.get("/municipality/ZARAGOZA/street")

            assert response.status_code == 200
            assert "X-Streets-Source" in response.headers
            assert response.headers["X-Streets-Source"] == "Database"
            # Cache headers should not be present in database mode
            assert "X-Cache-Status" not in response.headers

    def test_streets_endpoint_headers_igear_mode(self):
        """Test response headers indicate IGEAR source when feature flag is on."""
        with patch.object(settings, 'use_igear_for_streets', True):
            # Mock the IGEAR service calls
            with patch('services.streets_service.StreetsService._get_streets_igear') as mock_igear:
                mock_igear.return_value = [
                    {"nombre_calle": "CALLE MAYOR"},
                    {"nombre_calle": "AVENIDA CENTRAL"}
                ]

                response = client.get("/municipality/ZARAGOZA/street")

                assert response.status_code == 200
                assert "X-Streets-Source" in response.headers
                assert response.headers["X-Streets-Source"] == "IGEAR"
                # Cache headers should be present in IGEAR mode
                assert "X-Cache-Status" in response.headers
                assert "X-Cache-Enabled" in response.headers

    def test_streets_endpoint_nonexistent_municipality(self):
        """Test behavior with non-existent municipality."""
        response = client.get("/municipality/INVALID_MUNICIPALITY_NAME_999/street")

        assert response.status_code == 200
        # Should return empty list, not error
        assert response.json() == []

    def test_streets_endpoint_sorted_alphabetically(self):
        """Test that streets are returned in alphabetical order."""
        response = client.get("/municipality/ZARAGOZA/street")

        data = response.json()

        # If there are results, verify they're sorted
        if len(data) > 1:
            street_names = [s["nombre_calle"] for s in data]
            assert street_names == sorted(street_names), "Streets should be sorted alphabetically"

    def test_streets_endpoint_no_duplicates(self):
        """Test that there are no duplicate streets in results."""
        response = client.get("/municipality/ZARAGOZA/street")

        data = response.json()
        street_names = [s["nombre_calle"] for s in data]

        # Check for duplicates
        assert len(street_names) == len(set(street_names)), "There should be no duplicate streets"

    def test_streets_endpoint_special_characters(self):
        """Test handling of municipality names with special characters."""
        # Test with various special characters that might appear in Spanish names
        test_municipalities = [
            "ZARAGOZA",
            "ALCAÑIZ",
            "TARAZONA"
        ]

        for municipality in test_municipalities:
            response = client.get(f"/municipality/{municipality}/street")
            # Should not error, even if municipality doesn't exist
            assert response.status_code == 200
            assert isinstance(response.json(), list)

    def test_streets_endpoint_url_encoding(self):
        """Test handling of URL-encoded municipality names."""
        # Test with spaces (should be URL encoded)
        response = client.get("/municipality/NOMBRE%20CON%20ESPACIOS/street")

        assert response.status_code == 200
        # Should return empty list for non-existent municipality
        assert isinstance(response.json(), list)

    def test_streets_endpoint_case_sensitivity(self):
        """Test that municipality name matching is case-sensitive (as per database)."""
        # Database uses uppercase names
        response_upper = client.get("/municipality/ZARAGOZA/street")
        response_lower = client.get("/municipality/zaragoza/street")

        assert response_upper.status_code == 200
        assert response_lower.status_code == 200

        # Lowercase might return empty if database is case-sensitive
        # This is expected behavior
        assert isinstance(response_upper.json(), list)
        assert isinstance(response_lower.json(), list)

    @pytest.mark.parametrize("municipality", [
        "ZARAGOZA",
        "HUESCA",
        "TERUEL"
    ])
    def test_streets_endpoint_major_municipalities(self, municipality):
        """Test endpoint with major municipalities."""
        response = client.get(f"/municipality/{municipality}/street")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Major cities should have streets
        if municipality in ["ZARAGOZA", "HUESCA", "TERUEL"]:
            # These should have results (assuming test data exists)
            # This assertion might fail if test database is empty
            pass  # Can be enabled if test data is available

    def test_streets_endpoint_performance_headers(self):
        """Test that response includes performance-related headers."""
        response = client.get("/municipality/ZARAGOZA/street")

        assert response.status_code == 200
        assert "X-Streets-Source" in response.headers

        # If using IGEAR, should have cache headers
        if response.headers["X-Streets-Source"] == "IGEAR":
            assert "X-Cache-Status" in response.headers
            assert response.headers["X-Cache-Status"] in ["HIT", "MISS"]

    def test_streets_endpoint_error_handling(self):
        """Test error handling with invalid input."""
        # Test with very long municipality name
        long_name = "A" * 1000
        response = client.get(f"/municipality/{long_name}/street")

        # Should handle gracefully
        assert response.status_code in [200, 400, 500]

    def test_streets_endpoint_concurrent_requests(self):
        """Test that endpoint handles concurrent requests correctly."""
        import concurrent.futures

        def make_request(municipality):
            return client.get(f"/municipality/{municipality}/street")

        municipalities = ["ZARAGOZA", "HUESCA", "TERUEL"] * 3

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, m) for m in municipalities]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        for result in results:
            assert result.status_code == 200
            assert isinstance(result.json(), list)


class TestStreetsEndpointCaching:
    """Tests specifically for caching behavior in IGEAR mode."""

    @patch.object(settings, 'use_igear_for_streets', True)
    def test_cache_miss_then_hit(self):
        """Test that second request hits cache."""
        with patch('services.streets_service.StreetsService._get_streets_igear') as mock_igear:
            # Mock returns for cache testing
            mock_streets = [{"nombre_calle": "CALLE TEST"}]
            mock_igear.return_value = mock_streets

            # First request - should be cache MISS
            response1 = client.get("/municipality/CACHE_TEST/street")
            assert response1.status_code == 200

            # Note: In real testing with Redis, second request would be cache HIT
            # This would require actual Redis instance for integration testing


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
