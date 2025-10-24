"""
Script to fetch the complete fianzas layer from IGEAR SITA WMS service.

This script queries the WFS service to retrieve all rental data features
and saves them as a GeoJSON file.
"""
import requests
import json
import time
from datetime import datetime

# IGEAR Service Configuration
SITA_WMS_URL = "https://idearagon.aragon.es/SITA_WMS"
LAYER = "fianzas"
WFS_VERSION = "1.1.0"
WFS_OUTPUT_FORMAT = "application/json"
EPSG_CODE = "EPSG:25830"
REQUEST_TIMEOUT = 300  # 5 minutes for large dataset

# Output file
OUTPUT_FILE = "fianzas_wfs_layer.json"


def fetch_all_fianzas_features():
    """
    Fetch all features from the fianzas layer using WFS GetFeature.

    This makes a single request to get ALL features without any filter.

    Returns:
        dict: GeoJSON response with all features
    """
    print("="*70)
    print("Fetching Complete Fianzas Layer from IGEAR SITA WMS")
    print("="*70)
    print(f"Service URL: {SITA_WMS_URL}")
    print(f"Layer: {LAYER}")
    print(f"Output Format: {WFS_OUTPUT_FORMAT}")
    print(f"Output File: {OUTPUT_FILE}")
    print()

    # WFS GetFeature request parameters
    params = {
        'service': 'WFS',
        'version': WFS_VERSION,
        'request': 'GetFeature',
        'typename': LAYER,
        'outputFormat': WFS_OUTPUT_FORMAT,
        'srsname': EPSG_CODE
        # No CQL_FILTER = get all features
    }

    print("[REQUEST PARAMETERS]")
    for key, value in params.items():
        print(f"  {key}: {value}")
    print()

    try:
        print(f"[SENDING REQUEST] Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("This may take several minutes for the complete dataset...")
        print()

        start_time = time.time()

        # Make POST request
        response = requests.post(
            SITA_WMS_URL,
            data=params,
            timeout=REQUEST_TIMEOUT
        )

        elapsed = time.time() - start_time

        print(f"[RESPONSE RECEIVED] Completed in {elapsed:.2f} seconds")
        print(f"  Status Code: {response.status_code}")
        print(f"  Response Size: {len(response.text):,} bytes ({len(response.text)/1024/1024:.2f} MB)")
        print()

        if response.status_code != 200:
            print(f"[ERROR] Non-200 status code received")
            print(f"Response preview: {response.text[:500]}")
            return None

        # Parse JSON
        print("[PARSING JSON]...")
        data = response.json()

        # Get feature count
        num_features = len(data.get('features', []))
        print(f"[SUCCESS] ✓ Parsed {num_features:,} features")
        print()

        # Show sample feature structure
        if num_features > 0:
            print("[SAMPLE FEATURE]")
            sample = data['features'][0]
            print(f"  Type: {sample.get('type')}")
            print(f"  Properties keys: {list(sample.get('properties', {}).keys())}")
            if 'properties' in sample:
                via_loc = sample['properties'].get('via_loc', 'N/A')
                print(f"  Sample via_loc: {via_loc}")
            print()

        return data

    except requests.Timeout:
        print(f"[ERROR] Request timed out after {REQUEST_TIMEOUT} seconds")
        print("The dataset might be too large. Consider:")
        print("  1. Increasing REQUEST_TIMEOUT")
        print("  2. Fetching data in batches by municipality")
        return None

    except requests.RequestException as e:
        print(f"[ERROR] Request failed: {e}")
        return None

    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse JSON response: {e}")
        print(f"Response preview: {response.text[:500]}")
        return None

    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return None


def save_to_file(data, filename):
    """
    Save GeoJSON data to file.

    Args:
        data: GeoJSON data dictionary
        filename: Output filename

    Returns:
        bool: True if successful, False otherwise
    """
    print(f"[SAVING] Writing data to {filename}...")

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=None)

        # Get file size
        import os
        file_size = os.path.getsize(filename)

        print(f"[SUCCESS] ✓ File saved successfully")
        print(f"  File: {filename}")
        print(f"  Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
        print()

        return True

    except Exception as e:
        print(f"[ERROR] Failed to save file: {e}")
        return False


def main():
    """Main execution function."""
    print()
    print("╔" + "="*68 + "╗")
    print("║" + " "*20 + "FIANZAS LAYER FETCHER" + " "*27 + "║")
    print("╚" + "="*68 + "╝")
    print()

    # Fetch data
    data = fetch_all_fianzas_features()

    if data is None:
        print()
        print("[FAILED] ✗ Could not fetch fianzas layer data")
        print()
        return 1

    # Save to file
    success = save_to_file(data, OUTPUT_FILE)

    if not success:
        print()
        print("[FAILED] ✗ Could not save data to file")
        print()
        return 1

    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"✓ Successfully fetched and saved fianzas layer")
    print(f"✓ Total features: {len(data.get('features', [])):,}")
    print(f"✓ Output file: {OUTPUT_FILE}")
    print()
    print("You can now copy this file to the app directories:")
    print(f"  cp {OUTPUT_FILE} streamlit/")
    print(f"  cp {OUTPUT_FILE} dash/")
    print(f"  cp {OUTPUT_FILE} dash-json/")
    print()

    return 0


if __name__ == '__main__':
    exit(main())
