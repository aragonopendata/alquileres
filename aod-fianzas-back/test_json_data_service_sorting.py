#!/usr/bin/env python3
"""
Unit test to verify JsonDataService sorting matches database behavior.

This test ensures that the sorting in get_stats_by_street_and_municipality()
produces the exact same order as the database query:
    ORDER BY anyo DESC, eslocal DESC

Expected behavior:
- Years in descending order (2024, 2023, 2022...)
- Within each year, 'Vivienda' before 'Local' (alphabetical DESC)
"""

import json
import os
import tempfile
from services.json_data_service import JsonDataService


def test_sorting_matches_database_behavior():
    """Test that sorting matches ORDER BY anyo DESC, eslocal DESC."""

    # Create test data with deliberately unsorted valores
    test_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "objectid": 1,
                    "via_loc": "Calle Test (TestCity)",
                    "valores": [
                        {"anyo": 2022, "tipo": 2, "min": 200, "max": 300, "media": 250, "num": 5},  # Local
                        {"anyo": 2024, "tipo": 1, "min": 400, "max": 500, "media": 450, "num": 10}, # Vivienda
                        {"anyo": 2023, "tipo": 2, "min": 250, "max": 350, "media": 300, "num": 7},  # Local
                        {"anyo": 2024, "tipo": 2, "min": 300, "max": 400, "media": 350, "num": 8},  # Local
                        {"anyo": 2021, "tipo": 1, "min": 150, "max": 250, "media": 200, "num": 3},  # Vivienda
                        {"anyo": 2023, "tipo": 1, "min": 350, "max": 450, "media": 400, "num": 9},  # Vivienda
                        {"anyo": 2022, "tipo": 1, "min": 250, "max": 350, "media": 300, "num": 6},  # Vivienda
                        {"anyo": 2021, "tipo": 2, "min": 100, "max": 200, "media": 150, "num": 2},  # Local
                    ]
                },
                "geometry": {"type": "Point", "coordinates": [0, 0]}
            }
        ]
    }

    # Create temporary JSON file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_data, f)
        temp_file = f.name

    try:
        # Initialize service with test data
        service = JsonDataService(json_file_path=temp_file)

        # Query statistics
        stats = service.get_stats_by_street_and_municipality("Calle Test", "TestCity")

        # Verify we got all 8 records
        assert len(stats) == 8, f"Expected 8 records, got {len(stats)}"

        # Expected order matching database: ORDER BY anyo DESC, eslocal DESC
        expected_order = [
            (2024, "Vivienda"),  # Highest year, Vivienda first
            (2024, "Local"),     # Highest year, Local second
            (2023, "Vivienda"),
            (2023, "Local"),
            (2022, "Vivienda"),
            (2022, "Local"),
            (2021, "Vivienda"),
            (2021, "Local"),     # Lowest year, Local last
        ]

        # Extract actual order
        actual_order = [(s['anyo'], s['eslocal']) for s in stats]

        # Verify order matches
        print("Expected order:")
        for year, tipo in expected_order:
            print(f"  {year} {tipo}")

        print("\nActual order:")
        for year, tipo in actual_order:
            print(f"  {year} {tipo}")

        assert actual_order == expected_order, (
            f"Sorting does not match database behavior!\n"
            f"Expected: {expected_order}\n"
            f"Actual: {actual_order}"
        )

        print("\n✓ SUCCESS: Sorting matches database ORDER BY anyo DESC, eslocal DESC")

        # Verify data integrity (spot check a few records)
        assert stats[0]['anyo'] == 2024
        assert stats[0]['eslocal'] == "Vivienda"
        assert stats[0]['media_renta'] == 450

        assert stats[1]['anyo'] == 2024
        assert stats[1]['eslocal'] == "Local"
        assert stats[1]['media_renta'] == 350

        assert stats[-1]['anyo'] == 2021
        assert stats[-1]['eslocal'] == "Local"
        assert stats[-1]['media_renta'] == 150

        print("✓ Data integrity verified")

        return True

    finally:
        # Clean up temp file
        os.unlink(temp_file)


if __name__ == "__main__":
    test_sorting_matches_database_behavior()
    print("\n" + "="*70)
    print("All tests passed!")
    print("="*70)
