#!/usr/bin/env python3
"""
Simple launcher script for the Caption Generator GUI.
This script provides a convenient way to start the GUI with error handling.
"""

import sys
import subprocess
import os

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import gradio
        import yaml
        print("✅ Dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        return False

def main():
    print("🚀 Caption Generator GUI Launcher")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists("caption.yaml"):
        print("⚠️  Warning: caption.yaml not found in current directory")
        print("   Make sure you're running this from the project root directory")
        exit(1)
    
    # Check dependencies
    if not check_dependencies():
        input("Dependencies could not be loaded. Something is wrong with install")
        exit(1)
        return
    
    print("Starting GUI...")
    try:
        # Import and run the GUI
        from caption_gui import main as gui_main
        gui_main()
    except KeyboardInterrupt:
        print("\n👋 GUI stopped by user")
    except Exception as e:
        print(f"❌ Error starting GUI: {e}")
        print("Make sure all dependencies are installed and try again")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
