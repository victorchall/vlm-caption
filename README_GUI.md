# Caption Generator GUI

A user-friendly Gradio interface for the image captioning script.

## Features

- **YAML Configuration Editor**: Edit your caption.yaml configuration directly in the GUI
- **Dynamic Hint Sources**: Automatically detects available hint sources and provides checkboxes to enable/disable them
- **Directory Selection**: Easy selection of base directory and recursive search options
- **Live Output**: Real-time display of script output during caption generation
- **Process Control**: Start and stop caption generation processes
- **Cross-platform**: Works on both Windows and Linux

## Installation

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the GUI:
   ```bash
   python caption_gui.py
   ```

3. Open your browser and navigate to: http://localhost:7860

## Usage

### Configuration Tab
1. Edit your YAML configuration directly or use the form controls
2. Set the base directory containing your images
3. Choose whether to search recursively
4. Select which hint sources to enable
5. Save your configuration

### Run Tab
1. Click "Start Caption Generation" to begin processing
2. Monitor the live output for progress
3. Use "Stop" button to halt processing if needed

### Help Tab
- View available hint sources and their descriptions
- Read usage instructions

## Adding New Hint Sources

To add a new hint source:

1. Add your hint function to `hints/hint_sources.py`
2. Register it in `hints/registration.py` by adding it to:
   - `HINT_FUNCTIONS` dictionary
   - `get_available_hint_sources()` for display name
   - `get_hint_source_descriptions()` for description

The GUI will automatically detect and display the new hint source with a checkbox.

## Architecture

- **caption_gui.py**: Main GUI application using Gradio
- **hints/registration.py**: Centralized hint source registration
- **hints/hint_sources.py**: Individual hint source implementations
- **caption_openai.py**: Original CLI script (unchanged)

The original `caption_openai.py` script remains fully functional and can be run independently of the GUI.

## Requirements

- Python 3.8+
- All packages listed in requirements.txt
- Your existing caption.yaml configuration file
