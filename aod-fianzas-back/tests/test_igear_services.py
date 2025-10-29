"""
Test script to investigate IGEAR services and understand data structure.
"""
import json
from services.igear_service import IgearService
from config import settings

def test_municipality_search():
    """Test searching for a municipality using typed search."""
    print("=" * 80)
    print("TESTING MUNICIPALITY SEARCH")
    print("=" * 80)

    igear = IgearService()

    # Test with a known municipality
    test_municipalities = ["Zaragoza", "Huesca", "Teruel"]

    for muni in test_municipalities:
        print(f"\n--- Searching for municipality: {muni} ---")
        try:
            xml_response = igear.typed_search_service(
                texto=muni,
                search_type=settings.typed_search_localidad
            )

            # Extract object ID
            list_elements = xml_response.xpath('//List')
            if list_elements and list_elements[0].text:
                parts = list_elements[0].text.split('#')
                print(f"  Full response: {list_elements[0].text}")
                print(f"  Parts: {parts}")
                if len(parts) > 3:
                    object_id = parts[3]
                    print(f"  Object ID: {object_id}")
                    print(f"  Typename: {settings.typename_localidad}")

                    # Now test spatial search with this ID
                    test_spatial_search(object_id, settings.typename_localidad, muni)
        except Exception as e:
            print(f"  Error: {e}")

def test_spatial_search(object_id: str, typename: str, label: str):
    """Test spatial search with an object ID."""
    print(f"\n  >>> Testing spatial search for {label} (ID: {object_id})")

    igear = IgearService()

    try:
        spatial_results = igear.spatial_search_service(object_id, typename)
        print(f"  Found {len(spatial_results.resultados)} spatial results")

        for i, resultado in enumerate(spatial_results.resultados):
            print(f"\n  --- Result {i+1} ---")
            print(f"    Layer: {resultado.capa}")
            print(f"    Distance: {resultado.distancia}")
            print(f"    Features: {len(resultado.feature_collection.features)}")

            # Check if it's the 'fianzas' layer
            if 'fianzas' in resultado.capa.lower():
                print(f"\n    *** FIANZAS LAYER FOUND ***")
                test_wfs_features(resultado, object_id)

    except Exception as e:
        print(f"  Spatial search error: {e}")

def test_wfs_features(spatial_resultado, object_id: str):
    """Test getting WFS features for fianzas layer."""
    print(f"\n    >>> Testing WFS feature retrieval")

    igear = IgearService()

    try:
        # Build CQL filter from spatial results
        cql_filter = ""
        for feature in spatial_resultado.feature_collection.features:
            feature_oid = feature.properties.get('objectid')
            if feature_oid:
                if cql_filter:
                    cql_filter += f" OR objectid={feature_oid}"
                else:
                    cql_filter = f"objectid={feature_oid}"

        if not cql_filter:
            print("    No CQL filter could be built")
            return

        print(f"    CQL Filter: {cql_filter[:200]}...")  # Truncate if too long

        # Get WFS features
        wfs_response = igear.sita_wms_get_feature(
            typename="fianzas",
            cql_filter=cql_filter
        )

        print(f"    Total features: {wfs_response.total_features}")
        print(f"    Features count: {len(wfs_response.features)}")

        # Examine first few features
        for i, feature in enumerate(wfs_response.features[:3]):
            print(f"\n    --- Feature {i+1} ---")
            print(f"      ID: {feature.id}")
            print(f"      Properties:")
            props = feature.properties.model_dump()
            for key, value in props.items():
                if value is not None:
                    value_str = str(value)
                    if len(value_str) > 100:
                        value_str = value_str[:100] + "..."
                    print(f"        {key}: {value_str}")

            # Focus on 'valores' field
            if feature.properties.valores:
                print(f"\n      *** VALORES FIELD ANALYSIS ***")
                print(f"      Raw valores: {feature.properties.valores[:500]}")
                try:
                    # Try to parse if it's JSON
                    valores_data = json.loads(feature.properties.valores)
                    print(f"      Parsed valores (JSON):")
                    print(f"      {json.dumps(valores_data, indent=8)[:500]}")
                except:
                    print(f"      valores is not JSON, might be plain text or other format")

    except Exception as e:
        print(f"    WFS features error: {e}")
        import traceback
        traceback.print_exc()

def test_street_search():
    """Test searching for streets in a municipality."""
    print("\n\n" + "=" * 80)
    print("TESTING STREET SEARCH")
    print("=" * 80)

    igear = IgearService()

    # Test with a known street and municipality
    test_cases = [
        ("COSO", "Zaragoza"),
        ("MAYOR", "Huesca"),
    ]

    for street, municipality in test_cases:
        print(f"\n--- Searching for street: {street} in {municipality} ---")
        try:
            xml_response = igear.typed_search_service(
                texto=street,
                search_type=settings.typed_search_direccion,
                muni=municipality
            )

            # Extract c_mun_via
            list_elements = xml_response.xpath('//List')
            if list_elements:
                for i, elem in enumerate(list_elements[:5]):  # Show first 5 results
                    if elem.text:
                        parts = elem.text.split('#')
                        print(f"  Result {i+1}: {elem.text}")
                        if len(parts) > 3:
                            c_mun_via = parts[3]
                            street_name = parts[0] if len(parts) > 0 else "N/A"
                            print(f"    Street name: {street_name}")
                            print(f"    c_mun_via: {c_mun_via}")

                            # Try to get features for this street
                            if i == 0:  # Only test first result
                                test_street_features(c_mun_via, street, municipality)
        except Exception as e:
            print(f"  Error: {e}")

def test_street_features(c_mun_via: str, street: str, municipality: str):
    """Test getting features for a specific street."""
    print(f"\n  >>> Testing feature retrieval for street")

    igear = IgearService()

    try:
        cql_filter = f"c_mun_via='{c_mun_via}'"

        # Get from visor2d service
        wfs_response = igear.visor2d_service(
            typename=settings.typed_search_direccion,
            cql_filter=cql_filter
        )

        print(f"  Total features from visor2d: {wfs_response.total_features}")

        if wfs_response.features:
            feature = wfs_response.features[0]
            print(f"  First feature:")
            print(f"    objectid: {feature.properties.objectid}")
            print(f"    via_loc: {feature.properties.via_loc}")

            # Now try to get fianzas data for this street
            if feature.properties.objectid:
                test_street_fianzas(str(feature.properties.objectid), settings.typename_direccion, street)

    except Exception as e:
        print(f"  Error getting street features: {e}")

def test_street_fianzas(object_id: str, typename: str, street: str):
    """Test getting fianzas data for a street."""
    print(f"\n  >>> Testing fianzas data for street (objectid: {object_id})")

    igear = IgearService()

    try:
        # Get spatial search results
        spatial_results = igear.spatial_search_service(object_id, typename)
        print(f"  Found {len(spatial_results.resultados)} spatial results")

        for resultado in spatial_results.resultados:
            if 'fianzas' in resultado.capa.lower() and resultado.distancia == 1000:
                print(f"    Found fianzas layer with distance 1000")
                print(f"    Features in spatial result: {len(resultado.feature_collection.features)}")

                # Build CQL filter and get actual WFS features
                cql_filter = ""
                for feature in resultado.feature_collection.features:
                    feature_oid = feature.properties.get('objectid')
                    if feature_oid:
                        if cql_filter:
                            cql_filter += f" OR objectid={feature_oid}"
                        else:
                            cql_filter = f"objectid={feature_oid}"

                if cql_filter:
                    wfs_response = igear.sita_wms_get_feature("fianzas", cql_filter)
                    print(f"    WFS features retrieved: {len(wfs_response.features)}")

                    # Show first feature's valores
                    if wfs_response.features:
                        feature = wfs_response.features[0]
                        print(f"\n    First feature valores:")
                        if feature.properties.valores:
                            print(f"    {feature.properties.valores[:300]}...")
                break

    except Exception as e:
        print(f"  Error getting street fianzas: {e}")

if __name__ == "__main__":
    try:
        test_municipality_search()
        test_street_search()
        print("\n" + "=" * 80)
        print("Investigation complete!")
        print("=" * 80)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
