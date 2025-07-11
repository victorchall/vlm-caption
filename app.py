from flask import Flask, jsonify, request
from flask_cors import CORS
import asyncio
import threading
import io
import sys
import argparse
import yaml
import json
import os
from caption_openai import main as caption_main
from hints.registration import get_available_hint_sources, get_hint_source_descriptions

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

@app.route('/api/hint_sources', methods=['GET'])
def get_hint_sources():
    """Get available hint sources and their descriptions"""
    try:
        # Get available hint sources
        hint_sources = get_available_hint_sources()
        descriptions = get_hint_source_descriptions()

        # Combine the data for the response
        hint_sources_data = {}
        for source, display_name in hint_sources.items():
            hint_sources_data[source] = {
                'display_name': display_name,
                'description': descriptions.get(source, '')
            }

        return jsonify({
            'success': True,
            'hint_sources': hint_sources_data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get hint sources: {str(e)}'
        }), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration from caption.yaml"""
    try:
        config_path = 'caption.yaml'
        
        # Check if config file exists
        if not os.path.exists(config_path):
            return jsonify({'error': 'Configuration file not found'}), 404
        
        # Load YAML configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return jsonify({
            'success': True,
            'config': config
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to load configuration: {str(e)}'
        }), 500

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration and save to caption.yaml"""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No configuration data provided'}), 400
        
        new_config = data.get('config')
        if not new_config:
            return jsonify({'error': 'No config object provided'}), 400
        
        config_path = 'caption.yaml'
        
        # Read current configuration
        current_config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                current_config = yaml.safe_load(f) or {}
            
            # Create backup of current config
            backup_path = f"{config_path}.backup"
            with open(config_path, 'r', encoding='utf-8') as src, open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        
        # Merge new config with existing config
        merged_config = current_config.copy()
        merged_config.update(new_config)
        
        # Save merged configuration to YAML
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(merged_config, f, default_flow_style=False, sort_keys=False)
        
        actual_saved_path = os.path.abspath(config_path)
        return jsonify({
            'success': True,
            'message': f'Configuration saved to {actual_saved_path}'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to save configuration: {str(e)}'
        }), 500

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--port", type=int, default=5000)
    args = argparser.parse_args()

    # Only enable debug mode if running from source (not packaged)
    debug_mode = not getattr(sys, 'frozen', False)
    app.run(debug=debug_mode, host='0.0.0.0', port=args.port)
