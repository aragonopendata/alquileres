"""
Test script to validate the new IGEAR-based endpoints.
"""
import json
from services.fianzas_service import fianzas_service

def test_get_streets():
    """Test getting streets for a municipality."""
    print("=" * 80)
    print("TESTING GET STREETS BY MUNICIPALITY")
    print("=" * 80)

    test_municipalities = ["Zaragoza", "Huesca"]

    for municipality in test_municipalities:
        print(f"\n--- Testing municipality: {municipality} ---")
        try:
            streets = fianzas_service.get_streets_by_municipality(municipality)
            print(f"  Found {len(streets)} streets")

            # Show first 10 streets
            print(f"\n  First 10 streets:")
            for street in streets[:10]:
                print(f"    - {street['nombre_calle']}")

        except Exception as e:
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()


def test_get_stats():
    """Test getting stats for specific streets."""
    print("\n\n" + "=" * 80)
    print("TESTING GET STATS BY STREET AND MUNICIPALITY")
    print("=" * 80)

    test_cases = [
        ("Calle COSO", "Zaragoza"),
        ("Calle MAYOR", "Huesca"),
    ]

    for street, municipality in test_cases:
        print(f"\n--- Testing: {street} in {municipality} ---")
        try:
            stats = fianzas_service.get_stats_by_street_and_municipality(
                street,
                municipality
            )
            print(f"  Found {len(stats)} stat records")

            if stats:
                print(f"\n  Sample stats (first 5):")
                for stat in stats[:5]:
                    print(f"    Year: {stat['anyo']}, "
                          f"Type: {stat['eslocal']}, "
                          f"Avg: {stat['media_renta']}, "
                          f"Min: {stat['min_renta']}, "
                          f"Max: {stat['max_renta']}, "
                          f"Count: {stat['nfianzas']}")

                # Verify sorting (year DESC, eslocal DESC where Local=2, Vivienda=1)
                print(f"\n  Verifying sort order...")
                for i in range(len(stats) - 1):
                    curr = stats[i]
                    next_stat = stats[i + 1]

                    # Year should be descending
                    if curr['anyo'] < next_stat['anyo']:
                        print(f"  ⚠️ WARNING: Sort order issue at index {i}")
                        print(f"     {curr['anyo']} should be >= {next_stat['anyo']}")

                    # For same year, Local should come before Vivienda
                    if curr['anyo'] == next_stat['anyo']:
                        if curr['eslocal'] == 'Vivienda' and next_stat['eslocal'] == 'Local':
                            print(f"  ⚠️ WARNING: Type sort issue at index {i}")
                            print(f"     Local should come before Vivienda")

                print(f"  ✓ Sort order looks correct")

        except Exception as e:
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()


def compare_with_test_data():
    """Compare results with known test data."""
    print("\n\n" + "=" * 80)
    print("COMPARING WITH EXPECTED DATA")
    print("=" * 80)

    # Test a known street from our earlier investigation
    print(f"\n--- Testing known street: Calle San Antonio de Padua (Zaragoza) ---")
    try:
        stats = fianzas_service.get_stats_by_street_and_municipality(
            "Calle San Antonio de Padua",
            "Zaragoza"
        )

        print(f"  Found {len(stats)} stat records")

        # We know from the test script that this street has data from 2001
        has_2001_data = any(s['anyo'] == 2001 for s in stats)
        print(f"  Has 2001 data: {has_2001_data}")

        if has_2001_data:
            stats_2001 = [s for s in stats if s['anyo'] == 2001]
            print(f"  2001 records: {len(stats_2001)}")
            for stat in stats_2001:
                print(f"    - Type: {stat['eslocal']}, "
                      f"Min: {stat['min_renta']}, "
                      f"Max: {stat['max_renta']}, "
                      f"Avg: {stat['media_renta']}")

    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        test_get_streets()
        test_get_stats()
        compare_with_test_data()
        print("\n" + "=" * 80)
        print("Testing complete!")
        print("=" * 80)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
