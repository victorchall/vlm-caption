# Caption Generator GUI

Rudimentary GUI for the caption script

## Features

- **YAML Configuration Editor**: Edit your caption.yaml configuration directly in the GUI, alternative to the first tab with checkboxes, probably not recommended
- **Dynamic Hint Sources**: Checkbox any additional metadata "hints"
- **Directory Selection**: Select the directory to scan with optional recursive (subdirectory) inclusion
- **Live Output**: Real-time display of script output during caption generation
- **Process Control**: Start and stop caption generation processes
- **Cross-platform**: Works on both Windows and Linux

## Installation

1. Install the required dependencies (one time)
   ```bash
   python -m venv venv
   .\venv\Scripts\activate.bat
   pip install -r requirements.txt
   ```

2. Run the GUI:
   ```bash
   .\venv\Scripts\activate.bat
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

If you can write basic Python or get an LLM to do it for you, see [HINTSOURCES.MD](HINTSOURCES.md)

