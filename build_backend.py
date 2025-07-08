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
    
    # Determine the project root directory (where this script and app.py are located)
    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir
    
    # Verify we found the correct root directory by checking for app.py
    if not (project_root / 'app.py').exists():
        print(f"Error: Could not find app.py in {project_root}")
        return False
    
    print(f"Project root directory: {project_root}")
    
    # Clean up any previous build (using absolute paths)
    build_dir = project_root / 'build'
    dist_dir = project_root / 'dist'
    
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    # PyInstaller command (using absolute paths for data files)
    caption_yaml = project_root / 'caption.yaml'
    character_info = project_root / 'character_info.txt'
    app_py = project_root / 'app.py'
    
    cmd = [
        'pyinstaller',
        '--onefile',
        '--name=app',
        f'--add-data={caption_yaml};.',
        f'--add-data={character_info};.',
        '--hidden-import=asyncio',
        '--hidden-import=flask',
        '--hidden-import=flask_cors',
        str(app_py)
    ]
    
    print("Building Flask backend with PyInstaller...")
    print(f"Command: {' '.join(cmd)}")
    print(f"Working directory: {project_root}")
    
    try:
        # Run PyInstaller from the project root directory
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=str(project_root))
        print("PyInstaller build completed successfully!")
        print(result.stdout)
        
        # Create the backend directory for Electron (using absolute path)
        backend_dir = project_root / 'ui/public/backend'
        backend_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy the executable to the backend directory (using absolute path)
        exe_path = dist_dir / 'app.exe'
        if exe_path.exists():
            shutil.copy2(exe_path, backend_dir / 'app.exe')
            print(f"Copied executable to {backend_dir / 'app.exe'}")
        else:
            print("Warning: app.exe not found in dist/ directory")
        
        # Copy necessary files to the backend directory (using absolute paths)
        files_to_copy = [caption_yaml, character_info]
        for file_path in files_to_copy:
            if file_path.exists():
                shutil.copy2(file_path, backend_dir / file_path.name)
                print(f"Copied {file_path.name} to backend directory")
            else:
                print(f"Warning: {file_path.name} not found")
        
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
