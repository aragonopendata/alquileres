#!/usr/bin/env python3
"""
Manual testing script for the streets endpoint.

Usage:
    python scripts/test_streets_endpoint_manual.py
    python scripts/test_streets_endpoint_manual.py --municipality HUESCA
    python scripts/test_streets_endpoint_manual.py --compare

Requirements:
    pip install httpx rich
"""
import httpx
import os
import sys
import argparse
from datetime import datetime
from typing import Dict, List


BASE_URL = os.getenv("API_URL", "http://localhost:8000")
TIMEOUT = 30.0


def test_municipality(municipality: str, verbose: bool = True) -> Dict:
    """
    Test streets endpoint for a municipality.

    Args:
        municipality: Municipality name to test
        verbose: Print detailed output

    Returns:
        Dictionary with test results
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f"Testing: {municipality}")
        print(f"{'='*60}")

    url = f"{BASE_URL}/municipality/{municipality}/street"
    results = {
        "municipality": municipality,
        "success": False,
        "error": None,
        "requests": []
    }

    try:
        # First request (cache miss if using IGEAR)
        if verbose:
            print(f"\n📍 Request 1: {url}")

        start = datetime.now()
        response1 = httpx.get(url, timeout=TIMEOUT)
        duration1 = (datetime.now() - start).total_seconds() * 1000

        request1_data = {
            "status": response1.status_code,
            "duration_ms": round(duration1, 2),
            "source": response1.headers.get('X-Streets-Source', 'Unknown'),
            "cache_status": response1.headers.get('X-Cache-Status', 'N/A'),
            "cache_enabled": response1.headers.get('X-Cache-Enabled', 'N/A'),
            "street_count": len(response1.json()) if response1.status_code == 200 else 0
        }
        results["requests"].append(request1_data)

        if verbose:
            print(f"  Status: {request1_data['status']}")
            print(f"  Duration: {request1_data['duration_ms']}ms")
            print(f"  Source: {request1_data['source']}")
            print(f"  Cache: {request1_data['cache_status']}")
            print(f"  Streets: {request1_data['street_count']}")

        # Second request (cache hit if using IGEAR)
        if verbose:
            print(f"\n📍 Request 2: {url}")

        start = datetime.now()
        response2 = httpx.get(url, timeout=TIMEOUT)
        duration2 = (datetime.now() - start).total_seconds() * 1000

        request2_data = {
            "status": response2.status_code,
            "duration_ms": round(duration2, 2),
            "source": response2.headers.get('X-Streets-Source', 'Unknown'),
            "cache_status": response2.headers.get('X-Cache-Status', 'N/A'),
            "street_count": len(response2.json()) if response2.status_code == 200 else 0
        }
        results["requests"].append(request2_data)

        if verbose:
            print(f"  Status: {request2_data['status']}")
            print(f"  Duration: {request2_data['duration_ms']}ms")
            print(f"  Cache: {request2_data['cache_status']}")

        # Show sample streets
        if response2.status_code == 200:
            streets = response2.json()
            results["success"] = True
            results["street_count"] = len(streets)

            if verbose and streets:
                print(f"\n📋 Sample streets (first 10):")
                for street in streets[:10]:
                    print(f"  • {street['nombre_calle']}")

                if len(streets) > 10:
                    print(f"  ... and {len(streets) - 10} more")

        # Performance analysis
        if verbose and len(results["requests"]) == 2:
            speedup = duration1 / duration2 if duration2 > 0 else 1
            print(f"\n⚡ Performance:")
            print(f"  Request 1: {duration1:.2f}ms")
            print(f"  Request 2: {duration2:.2f}ms")
            if request2_data['cache_status'] == 'HIT':
                print(f"  Speedup: {speedup:.2f}x (cache hit)")

    except httpx.TimeoutException:
        results["error"] = "Timeout"
        if verbose:
            print(f"\n❌ Error: Request timeout after {TIMEOUT}s")
    except httpx.HTTPError as e:
        results["error"] = str(e)
        if verbose:
            print(f"\n❌ Error: {e}")
    except Exception as e:
        results["error"] = str(e)
        if verbose:
            print(f"\n❌ Unexpected error: {e}")

    return results


def compare_municipalities(municipalities: List[str]):
    """
    Compare results across multiple municipalities.

    Args:
        municipalities: List of municipality names
    """
    print(f"\n{'='*80}")
    print("COMPARATIVE ANALYSIS")
    print(f"{'='*80}")

    all_results = []
    for municipality in municipalities:
        print(f"\n🔍 Testing {municipality}...")
        result = test_municipality(municipality, verbose=False)
        all_results.append(result)

        if result["success"]:
            req1 = result["requests"][0]
            req2 = result["requests"][1] if len(result["requests"]) > 1 else req1
            print(f"  ✅ {result.get('street_count', 0)} streets")
            print(f"     Source: {req1['source']}, "
                  f"First: {req1['duration_ms']}ms, "
                  f"Second: {req2['duration_ms']}ms")
        else:
            print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")

    # Summary table
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"{'Municipality':<20} {'Streets':>8} {'Source':>10} {'1st Req (ms)':>12} {'2nd Req (ms)':>12}")
    print(f"{'-'*80}")

    for result in all_results:
        if result["success"]:
            req1 = result["requests"][0]
            req2 = result["requests"][1] if len(result["requests"]) > 1 else req1
            print(f"{result['municipality']:<20} "
                  f"{result.get('street_count', 0):>8} "
                  f"{req1['source']:>10} "
                  f"{req1['duration_ms']:>12.2f} "
                  f"{req2['duration_ms']:>12.2f}")
        else:
            print(f"{result['municipality']:<20} {'ERROR':>8}")

    # Statistics
    successful = [r for r in all_results if r["success"]]
    if successful:
        avg_first = sum(r["requests"][0]["duration_ms"] for r in successful) / len(successful)
        avg_second = sum(r["requests"][1]["duration_ms"] for r in successful) / len(successful)
        total_streets = sum(r.get("street_count", 0) for r in successful)

        print(f"\n📊 Statistics:")
        print(f"  Successful: {len(successful)}/{len(all_results)}")
        print(f"  Total streets: {total_streets}")
        print(f"  Avg 1st request: {avg_first:.2f}ms")
        print(f"  Avg 2nd request: {avg_second:.2f}ms")

        # Detect if IGEAR mode is active
        if successful[0]["requests"][0]["source"] == "IGEAR":
            cache_hits = sum(1 for r in successful if r["requests"][1]["cache_status"] == "HIT")
            print(f"  Cache hit rate: {cache_hits}/{len(successful)} ({cache_hits/len(successful)*100:.1f}%)")


def check_health():
    """Check API health before running tests."""
    try:
        response = httpx.get(f"{BASE_URL}/health", timeout=10.0)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ API is healthy")
            print(f"   Database: {health['services']['database']}")
            print(f"   Cache: {health['services']['cache']}")
            return True
        else:
            print(f"⚠️  API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API at {BASE_URL}")
        print(f"   Error: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Manual testing script for streets endpoint"
    )
    parser.add_argument(
        "--municipality",
        "-m",
        help="Test specific municipality"
    )
    parser.add_argument(
        "--compare",
        "-c",
        action="store_true",
        help="Compare multiple municipalities"
    )
    parser.add_argument(
        "--url",
        help="API base URL (default: http://localhost:8000)"
    )

    args = parser.parse_args()

    # Override base URL if provided
    if args.url:
        global BASE_URL
        BASE_URL = args.url

    print(f"\n🚀 Streets Endpoint Tester")
    print(f"   API: {BASE_URL}")

    # Check health
    if not check_health():
        print("\n⚠️  Continuing anyway...\n")

    if args.compare:
        # Compare multiple municipalities
        municipalities = ["ZARAGOZA", "HUESCA", "TERUEL", "ALCAÑIZ", "TARAZONA"]
        compare_municipalities(municipalities)

    elif args.municipality:
        # Test single municipality
        test_municipality(args.municipality.upper())

    else:
        # Default: test ZARAGOZA
        print("\nℹ️  No municipality specified, testing ZARAGOZA")
        print("   Use --municipality to test specific municipality")
        print("   Use --compare to test multiple municipalities\n")
        test_municipality("ZARAGOZA")


if __name__ == "__main__":
    main()
