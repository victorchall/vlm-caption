from flask import Flask, jsonify, request
from flask_cors import CORS
import asyncio
import threading
import io
import sys
import argparse
from caption_openai import main as caption_main

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variable to track if captioning is running
captioning_in_progress = False

@app.route('/api/run', methods=['POST'])
def run_captioning():
    global captioning_in_progress
    
    if captioning_in_progress:
        return jsonify({'error': 'Captioning is already in progress'}), 400
    
    try:
        captioning_in_progress = True
        
        # Capture stdout to return as response
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()
        
        # Run the async main function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(caption_main())
        loop.close()
        
        # Get the captured output
        output = captured_output.getvalue()
        sys.stdout = old_stdout
        
        return jsonify({
            'success': True,
            'message': 'Captioning completed successfully',
            'output': output
        })
    
    except Exception as e:
        sys.stdout = old_stdout
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
    finally:
        captioning_in_progress = False

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        'captioning_in_progress': captioning_in_progress
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

def show_help():
    """Display help information and exit."""
    help_text = """
VLM Caption Flask Backend

Usage: app.exe [OPTIONS]

Options:
  --help    Show this help message and exit

This is the Flask backend server for VLM Caption.
When run without arguments, starts the server on http://localhost:5000

API Endpoints:
  POST /api/run     - Run captioning process
  GET  /api/status  - Check captioning status
  GET  /api/health  - Health check

The server provides a REST API interface for the VLM Caption functionality.
"""
    print(help_text.strip())
    sys.exit(0)

if __name__ == '__main__':
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help' or sys.argv[1] == '-h':
            show_help()
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Use --help for usage information")
            sys.exit(1)
    
    # Start the Flask server
    app.run(debug=True, host='0.0.0.0', port=5000)
