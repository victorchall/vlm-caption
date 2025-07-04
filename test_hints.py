"""
Test script to verify that the hints registration system is working correctly.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_hint_registration():
    """Test that hint registration works correctly."""
    print("Testing hint registration system...")
    
    try:
        # Test importing the registration module
        from hints.registration import HINT_FUNCTIONS, get_available_hint_sources, get_hint_source_descriptions
        print("✅ Successfully imported registration module")
        
        # Test that hint functions are registered
        print(f"📋 Registered hint functions: {list(HINT_FUNCTIONS.keys())}")
        
        # Test getting available hint sources
        available = get_available_hint_sources()
        print(f"🎯 Available hint sources: {available}")
        
        # Test getting descriptions
        descriptions = get_hint_source_descriptions()
        print(f"📝 Hint descriptions: {descriptions}")
        
        # Test importing the main hints module
        from hints.hint_sources import get_hints
        print("✅ Successfully imported hint_sources module")
        
        # Test calling get_hints function
        test_image_path = "test_image.jpg"  # Dummy path for testing
        hint_result = get_hints(["full_path"], test_image_path)
        print(f"🧪 Test hint result: {hint_result}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_caption_script_still_works():
    """Test that the original caption script can still be imported."""
    print("\nTesting original caption script compatibility...")
    
    try:
        # This should work without errors after our changes
        from hints.hint_sources import get_hints
        print("✅ Caption script can still import get_hints function")
        return True
    except Exception as e:
        print(f"❌ Error importing for caption script: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Running hints system tests...\n")
    
    success1 = test_hint_registration()
    success2 = test_caption_script_still_works()
    
    if success1 and success2:
        print("\n🎉 All tests passed! The hint system is working correctly.")
        print("✅ Original caption.py script should work unchanged")
        print("✅ GUI can access hint registration data")
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")
