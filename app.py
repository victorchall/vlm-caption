from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import asyncio
import threading
import io
import sys
import argparse
import yaml
import os
import queue
from caption_openai import main as caption_main
from hints.registration import get_available_hint_sources, get_hint_source_descriptions

app = Flask(__name__)
CORS(app)

captioning_in_progress = False
output_queue = queue.Queue()
current_task = None
task_lock = asyncio.Lock()

@app.route('/api/run', methods=['POST'])
def run_captioning():
    global captioning_in_progress, current_task

    if captioning_in_progress:
        return jsonify({'error': 'Captioning is already in progress'}), 400

    try:
        captioning_in_progress = True

        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()

        # Create a new event loop and run the task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Store the current task for potential cancellation
        current_task = loop.create_task(run_captioning_task())

        # Run until the task completes or is cancelled
        try:
            loop.run_until_complete(current_task)
        except asyncio.CancelledError:
            return jsonify({
                'success': False,
                'message': 'Captioning was cancelled by user'
            }), 200

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
        loop.close()

async def run_captioning_task():
    """Wrapper function for caption_main that handles cancellation"""
    try:
        await caption_main()
    except asyncio.CancelledError:
        print("Captioning task was cancelled")
        raise

@app.route('/api/stop', methods=['POST'])
def stop_captioning():
    global current_task

    if current_task is None or current_task.done():
        return jsonify({'error': 'No captioning process is currently running'}), 400

    try:
        # Cancel the task
        current_task.cancel()
        return jsonify({
            'success': True,
            'message': 'Captioning cancellation requested'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to cancel captioning: {str(e)}'
        }), 500

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
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No configuration data provided'}), 400
        
        new_config = data.get('config')
        if not new_config:
            return jsonify({'error': 'No config object provided'}), 400
        
        config_path = 'caption.yaml'
        
        current_config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                current_config = yaml.safe_load(f) or {}
            
            backup_path = f"{config_path}.backup"
            with open(config_path, 'r', encoding='utf-8') as src, open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        
        merged_config = current_config.copy()
        merged_config.update(new_config)
        
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

class StreamingStdout:
    """Custom stdout class that writes to both console and queue"""
    def __init__(self, original_stdout, output_queue):
        self.original_stdout = original_stdout
        self.output_queue = output_queue
        self.buffer = ""
    
    def write(self, text):
        # Write to original stdout
        self.original_stdout.write(text)
        self.original_stdout.flush()
        
        # Add to buffer and queue complete lines
        self.buffer += text
        while '\n' in self.buffer:
            line, self.buffer = self.buffer.split('\n', 1)
            self.output_queue.put(line + '\n')
    
    def flush(self):
        self.original_stdout.flush()

def run_captioning_with_streaming():
    global captioning_in_progress, output_queue, current_task

    try:
        captioning_in_progress = True

        # Clear any existing items in the queue
        while not output_queue.empty():
            try:
                output_queue.get_nowait()
            except queue.Empty:
                break

        original_stdout = sys.stdout
        sys.stdout = StreamingStdout(original_stdout, output_queue)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Store the current task for potential cancellation
        current_task = loop.create_task(run_captioning_task())

        # Run until the task completes or is cancelled
        try:
            loop.run_until_complete(current_task)
        except asyncio.CancelledError:
            output_queue.put("data: [CANCELLED] Captioning was cancelled by user\n\n")

        output_queue.put("data: [COMPLETE]\n\n")
        loop.close()

    except Exception as e:
        output_queue.put(f"data: [ERROR] {str(e)}\n\n")
    finally:
        sys.stdout = original_stdout
        captioning_in_progress = False

def generate_stream():
    """Generator function for Server-Sent Events"""
    global output_queue
    
    # Start captioning in a separate thread
    captioning_thread = threading.Thread(target=run_captioning_with_streaming)
    captioning_thread.daemon = True
    captioning_thread.start()
    
    # Send initial message
    yield "data: [STARTED] Captioning process started...\n\n"
    
    while True:
        try:
            output = output_queue.get(timeout=1)
            
            if output.startswith("data: [COMPLETE]"):
                yield output
                break
            elif output.startswith("data: [ERROR]"):
                yield output
                break
            else:
                yield f"data: {output.rstrip()}\n\n"
                
        except queue.Empty:
            # Send keepalive message
            yield "data: [KEEPALIVE]\n\n"
            
            # Check if thread is still alive
            if not captioning_thread.is_alive() and output_queue.empty():
                break
        except Exception as e:
            yield f"data: [ERROR] Stream error: {str(e)}\n\n"
            break

@app.route('/api/run-stream', methods=['GET'])
def run_captioning_stream():
    """Start captioning process with real-time streaming output"""
    global captioning_in_progress
    
    if captioning_in_progress:
        return jsonify({'error': 'Captioning is already in progress'}), 400
    
    return Response(generate_stream(), mimetype="text/event-stream")

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--port", type=int, default=5000)
    args = argparser.parse_args()

    # Only enable debug mode if running from source (not packaged)
    debug_mode = not getattr(sys, 'frozen', False)
    app.run(debug=debug_mode, host='0.0.0.0', port=args.port)
