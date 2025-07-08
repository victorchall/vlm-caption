# VLM Caption - Electron Desktop App

This document describes the Electron desktop application version of VLM Caption.

## Overview

The Electron version provides a desktop GUI application that packages both the React frontend and Flask backend into a single, self-contained executable installer for Windows.

## Architecture

- **Frontend**: React application (located in `ui/src/`)
- **Backend**: Flask API server (packaged as executable using PyInstaller)
- **Desktop Shell**: Electron application that manages both components

## Development Setup

### Prerequisites

- Python 3.x
- Node.js 18 or later
- npm

### Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install Node.js dependencies:
```bash
cd ui
npm install
```

### Running in Development Mode

1. Start the Flask backend:
```bash
python app.py
```

2. In a separate terminal, start the React development server with Electron:
```bash
cd ui
npm run electron-dev
```

This will:
- Start the React development server on http://localhost:3000
- Wait for the server to be ready
- Launch the Electron application

## Building for Production

### Build the Backend Executable

```bash
python build_backend.py
```

This creates a standalone executable at `ui/public/backend/app.exe` with all necessary dependencies.

### Build the Complete Electron App

```bash
cd ui
npm run build:electron
```

This will:
1. Build the Flask backend executable
2. Build the React application for production
3. Package everything into a Windows installer

The final installer will be created in `ui/dist/`.

## Project Structure

```
vlm-caption/
├── app.py                     # Flask backend
├── caption_openai.py          # Main caption script
├── build_backend.py           # Script to build backend executable
├── ui/
│   ├── public/
│   │   ├── electron.js        # Main Electron process
│   │   └── backend/           # Built backend executable (created during build)
│   ├── src/
│   │   ├── App.js             # React frontend
│   │   └── ...
│   ├── package.json           # Node.js dependencies and scripts
│   └── dist/                  # Built Electron app (created during build)
└── .github/workflows/
    └── build-release.yml      # Automated CI/CD workflow
```

## How It Works

1. **Electron Main Process** (`ui/public/electron.js`):
   - Creates the application window
   - Spawns the Flask backend process
   - Manages the application lifecycle

2. **Flask Backend**:
   - Packaged as a standalone executable using PyInstaller
   - Runs on localhost:5000
   - Provides the same API endpoints as the web version

3. **React Frontend**:
   - Built as a static application
   - Makes HTTP requests to the local Flask backend
   - Loaded into the Electron window

## Automated Builds

The GitHub Actions workflow (`.github/workflows/build-release.yml`) automatically builds both versions:

- **CLI Version**: `vlm-caption-cli.zip` - Traditional command-line tool
- **Desktop Version**: `VLM Caption Setup.exe` - Electron desktop installer

## Configuration

The Electron app uses the same configuration files as the CLI version:
- `caption.yaml` - Main configuration
- `character_info.txt` - Character information

These files are automatically included in the packaged application.

## Troubleshooting

### Backend Not Starting

If the desktop app fails to start, check:
1. Antivirus software isn't blocking the executable
2. All required files are present in the installation directory
3. Python dependencies are properly bundled

### API Connection Issues

If the frontend can't connect to the backend:
1. Check if port 5000 is available
2. Verify the Flask backend is starting correctly
3. Check the Electron console for error messages

## Development Notes

- The app uses `electron-is-dev` to detect development vs. production mode
- In development, it runs the Flask app directly with Python
- In production, it uses the packaged executable
- The `wait-on` utility ensures the backend is ready before loading the UI
