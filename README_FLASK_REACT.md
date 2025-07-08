# VLM Caption - Flask API + React UI

This document describes how to run the VLM Caption application with the new Flask API backend and React UI frontend.

## Prerequisites

- Python 3.7+ with venv
- Node.js 14+ and npm
- Your existing VLM Caption configuration (caption.yaml)

## Setup Instructions

### 1. Backend Setup (Flask API)

1. **Install Python dependencies:**
   ```bash
   # Activate your virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Start the Flask server:**
   ```bash
   python app.py
   ```
   
   The Flask server will run on `http://localhost:5000`

### 2. Frontend Setup (React UI)

1. **Install Node.js dependencies:**
   ```bash
   cd ui
   npm install
   ```

2. **Start the React development server:**
   ```bash
   npm start
   ```
   
   The React app will run on `http://localhost:3000`

## Usage

1. **Start both servers:**
   - In one terminal: Run `python app.py` (Flask backend)
   - In another terminal: Run `cd ui && npm start` (React frontend)

2. **Access the application:**
   - Open your browser and go to `http://localhost:3000`
   - Click the "Run Captioning" button to start the captioning process
   - The output will be displayed on the page

## API Endpoints

The Flask API provides the following endpoints:

- `POST /api/run` - Starts the captioning process
- `GET /api/status` - Returns the current status (whether captioning is running)
- `GET /api/health` - Health check endpoint

## Project Structure

```
vlm-caption/
├── app.py                 # Flask API server
├── caption_openai.py      # Original captioning script
├── caption.yaml           # Configuration file
├── requirements.txt       # Python dependencies
├── ui/                    # React frontend
│   ├── package.json       # Node.js dependencies
│   ├── public/
│   │   └── index.html     # HTML template
│   └── src/
│       ├── App.js         # Main React component
│       ├── App.css        # Styling
│       ├── index.js       # React entry point
│       └── index.css      # Global styles
└── README_FLASK_REACT.md  # This file
```

## Development Notes

- The React app uses a proxy configuration to communicate with the Flask backend
- The Flask server captures stdout to return the captioning output to the frontend
- CORS is enabled to allow the React development server to communicate with Flask
- The original `caption_openai.py` script can still be run directly if needed

## Building for Production

To build the React app for production:

```bash
cd ui
npm run build
```

This will create a `build` directory with optimized production files.

## Troubleshooting

- **Flask import errors:** Make sure your virtual environment is activated and all dependencies are installed
- **React build errors:** Ensure Node.js 14+ is installed and run `npm install` in the ui directory
- **CORS issues:** The Flask server includes CORS headers, but if you encounter issues, check that both servers are running on the expected ports
- **Connection refused:** Make sure the Flask server is running before starting the React app
