#!/usr/bin/env python3
"""
Script to build the Flask backend into a standalone executable using PyInstaller.
This script will be used both for local development and CI/CD.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_backend():
    """Build the Flask backend into a standalone executable."""
    
    # Clean up any previous build
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    
    # PyInstaller command
    cmd = [
        'pyinstaller',
        '--onefile',
        '--name=app',
        '--add-data=caption.yaml;.',
        '--add-data=character_info.txt;.',
        '--hidden-import=asyncio',
        '--hidden-import=flask',
        '--hidden-import=flask_cors',
        'app.py'
    ]
    
    print("Building Flask backend with PyInstaller...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("PyInstaller build completed successfully!")
        print(result.stdout)
        
        # Create the backend directory for Electron
        backend_dir = Path('ui/public/backend')
        backend_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy the executable to the backend directory
        exe_path = Path('dist/app.exe')
        if exe_path.exists():
            shutil.copy2(exe_path, backend_dir / 'app.exe')
            print(f"Copied executable to {backend_dir / 'app.exe'}")
        else:
            print("Warning: app.exe not found in dist/ directory")
        
        # Copy necessary files to the backend directory
        files_to_copy = ['caption.yaml', 'character_info.txt']
        for file in files_to_copy:
            if os.path.exists(file):
                shutil.copy2(file, backend_dir / file)
                print(f"Copied {file} to backend directory")
            else:
                print(f"Warning: {file} not found")
        
        # Create a simple test to verify the executable works
        print("\nTesting the built executable...")
        test_cmd = [str(backend_dir / 'app.exe'), '--help']
        try:
            subprocess.run(test_cmd, check=True, capture_output=True, text=True, timeout=10)
            print("Executable test passed!")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"Executable test failed: {e}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller build failed: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False

if __name__ == '__main__':
    success = build_backend()
    sys.exit(0 if success else 1)
