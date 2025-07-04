"""
Central registration system for hint source functions.
This module provides a centralized way to register and discover hint sources
for both the main captioning script and the GUI interface.
"""

import os
import json
from typing import Dict, Callable, Optional, Any

# Cache for metadata to avoid re-reading
_metadata_cache: Dict[str, Optional[Dict[str, Any]]] = {}


def get_full_path_hint(image_path: str, **kwargs) -> str:
    """
    Returns hint text with the full path information.
    
    Args:
        image_path: Full path to the image file
        **kwargs: Additional parameters (unused for this hint source)
        
    Returns:
        Formatted hint text with path information
    """
    normalized_path = os.path.normpath(image_path)
    
    hint_text = f"Image file information:\n"
    hint_text += f"- Full path: {normalized_path}\n"

    return hint_text

def get_json_hint(image_path: str, **kwargs) -> Optional[str]:
    """
    Returns hint text from the [image].json
    
    Args:
        image_path: Full path to the image file
        **kwargs: Additional parameters (unused for this hint source)
        
    Returns:
        Formatted hint text with path information
    """
    normalized_path = os.path.normpath(image_path)
    json_path = os.path.splitext(normalized_path)[0] + ".json"
    metadata = None

    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to read or parse {json_path}: {e}")
            metadata = None

    if metadata:    
        hint_text = f"Json Metadata:\n"
        hint_text += f"{json.dumps(metadata, indent=2)}\n"
        return hint_text

    return None

def get_metadata_hint(image_path: str, **kwargs) -> Optional[str]:
    """
    Reads metadata.json from the image's directory and includes it as context.
    Uses caching to avoid re-reading the same directory's metadata.
    
    Args:
        image_path: Full path to the image file
        **kwargs: Additional parameters (unused for this hint source)
        
    Returns:
        Formatted hint text with metadata information, or None if no metadata file exists
    """
    image_dir = os.path.dirname(os.path.normpath(image_path))
    
    if image_dir in _metadata_cache:
        metadata = _metadata_cache[image_dir]
    else:
        metadata_path = os.path.join(image_dir, "metadata.json")
        metadata = None
        
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Failed to read or parse metadata.json in {image_dir}: {e}")
                metadata = None
        
        # Cache the result (even if None)
        _metadata_cache[image_dir] = metadata
    
    # Return formatted hint if metadata exists
    if metadata:
        hint_text = "Directory metadata:\n"
        # Format metadata as key-value pairs
        for key, value in metadata.items():
            if isinstance(value, (list, dict)):
                hint_text += f"- {key}: {json.dumps(value)}\n"
            else:
                hint_text += f"- {key}: {value}\n"
        return hint_text
    
    return None


### Register hint sources in the following three functions ###

def get_available_hint_sources() -> Dict[str, str]:
    return {
        "full_path": "Full Path Information",
        "metadata": "Directory-lvel metadata.json",
        "json": "Image Json"
        # Display names can be customized here without affecting functionality
    }

def get_hint_source_descriptions() -> Dict[str, str]:
    return {
        "full_path": "Includes the full file path.",
        "metadata": "Reads metadata.json file from image's directory",
        "json": "Reads the [imagename].json file"
    }

HINT_FUNCTIONS: Dict[str, Callable] = {
    "full_path": get_full_path_hint,
    "metadata": get_metadata_hint,
    "json": get_json_hint
}

def _validate_hint_sources():
    """Verifies  hint code is properly configured with registrations"""
    available_hint_sources_keys = set(get_available_hint_sources().keys())
    hint_source_descriptions_keys = set(get_hint_source_descriptions().keys())
    hint_functions_keys = set(HINT_FUNCTIONS.keys())

    assert available_hint_sources_keys == hint_source_descriptions_keys == hint_functions_keys, "Hint sources not properly registered. Check source code."
