import sys
import time

def test_geocoder():
    print("Testing geocoder module...")

    try:
        from hints.gps import LocalGeocoder
        geocoder = LocalGeocoder("hints/gps/extracted_location_data.tsv")
        start_time = time.perf_counter()
        location_name, admin1_name, country = geocoder.query(35.360270, 138.726873)
        end_time = time.perf_counter()
        assert location_name == "Kenga-mine", "wrong location returned"
        assert admin1_name == "Shizuoka", "wrong prefecture returned"
        assert country == "Japan", "wrong country returned"
        query1_time = end_time - start_time
        print(f"Query time: {query1_time:.4f} seconds")
        print("✓ Geocoder works")
    except Exception as e:
        print(f"✗ Class-based approach failed: {e}")
        return False
    
    print("\nTest 2: Testing caching behavior")
    try:
        start_time = time.perf_counter()
        location_name, admin1_name, country = geocoder.query(40.7128, -74.0060)
        end_time = time.perf_counter()
        print(f"test2 result: {location_name, admin1_name, country}")
        assert location_name == "New York City Hall", "wrong location returned"
        assert admin1_name == "New York", "wrong city returned"
        assert country == "United States", "wrong country returned"
        query2_time = end_time - start_time
        print(f"Second query time: {query2_time:.4f} seconds")
        assert query2_time < (query1_time/1000), "Time should be significantly less on second call"
        print("✓ Caching works (second query should be lightning fast)")
    except Exception as e:
        print(f"✗ Caching test failed: {e}")
        print(type(e))
        return False
        
    print("\n🎉 Geocoder module is working correctly.")
    return True

if __name__ == "__main__":
    success = test_geocoder()
    sys.exit(0 if success else 1)
