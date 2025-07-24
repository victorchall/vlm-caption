"""
Central registration system for hint source functions.
This module provides a centralized way to register and discover hint sources
for both the main captioning script and the GUI interface.
"""

import os
import json
from typing import Dict, Callable, Optional, Any
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from .gps.local_geocoder import LocalGeocoder
import piexif

# Cache for metadata to avoid re-reading
_metadata_cache: Dict[str, Optional[Dict[str, Any]]] = {}
_geocoder: LocalGeocoder = LocalGeocoder()

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



def get_exif_hint(image_path: str, **kwargs) -> Optional[str]:
    """
    Extracts EXIF metadata from image files and includes it as context.
    
    Args:
        image_path: Full path to the image file
        **kwargs: Additional parameters (unused for this hint source)
        
    Returns:
        Formatted hint text with EXIF information, or None if no EXIF data exists
    """
    normalized_path = os.path.normpath(image_path)
    print("trying to get exif data")
    
    try:
        with Image.open(normalized_path) as img:
            exif_dict = piexif.load(img.info["exif"])

            #exif_data = img.getexif()
            # {296: 2, 282: 300.0, 34853: 926, 34665: 268, 270: 'cat pix ', 271: 'NIKON', 272: 'COOLPIX P6000', 305: 'Nikon Transfer 1.1 W', 274: 1, 306: '2008:11:01 21:15:07', 531: 1, 283: 300.0}
            
            if not exif_dict:
                return None
            if not "0th" in exif_dict:
                return None
            
            # Format the most useful EXIF data
            hint_text = "EXIF Metadata:\n"

            exif_ptr = exif_dict["0th"]
            
            # Camera information
            if piexif.ImageIFD.Make in exif_ptr and piexif.ImageIFD.Model in exif_ptr:
                hint_text += f"- Camera: {exif_ptr['Make']} {exif_ptr[piexif.ImageIFD.Model]}\n"
            elif piexif.ImageIFD.Make in exif_ptr:
                hint_text += f"- Camera Make: {exif_ptr[piexif.ImageIFD.Make]}\n"
            elif piexif.ImageIFD.Model in exif_ptr:
                hint_text += f"- Camera Model: {exif_ptr[piexif.ImageIFD.Model]}\n"
            
            # Date and time
            if piexif.ImageIFD.PreviewDateTime in exif_ptr:
                hint_text += f"- Date taken: {exif_ptr[piexif.ImageIFD.PreviewDateTime]}\n"
            elif piexif.ImageIFD.DateTime in exif_ptr:
                hint_text += f"- Date taken: {exif_ptr[piexif.ImageIFD.DateTime]}\n"
            
            # Camera settings
            if piexif.ExifIFD.ISOSpeed in exif_ptr:
                hint_text += f"- ISO: {exif_ptr[piexif.ExifIFD.ISOSpeed]}\n"
            elif piexif.ExifIFD.ISOSpeedRatings:
                hint_text += f"- ISO: {exif_ptr[piexif.ExifIFD.ISOSpeedRatings]}\n"
            
            if piexif.ExifIFD.FNumber in exif_ptr:
                f_number = exif_ptr[piexif.ExifIFD.FNumber]
                if isinstance(f_number, tuple) and len(f_number) == 2:
                    f_value = f_number[0] / f_number[1]
                    hint_text += f"- Aperture: f/{f_value:.1f}\n"
                else:
                    hint_text += f"- Aperture: f/{f_number}\n"
            
            if piexif.ExifIFD.ExposureTime in exif_ptr:
                exposure = exif_ptr[piexif.ExifIFD.ExposureTime]
                if isinstance(exposure, tuple) and len(exposure) == 2:
                    if exposure[0] == 1:
                        hint_text += f"- Shutter speed: 1/{exposure[1]}\n"
                    else:
                        hint_text += f"- Shutter speed: {exposure[0]}/{exposure[1]}\n"
                else:
                    hint_text += f"- Shutter speed: {exposure}\n"
            
            if piexif.ExifIFD.FocalLength in exif_ptr:
                focal_length = exif_ptr[piexif.ExifIFD.FocalLength]
                if isinstance(focal_length, tuple) and len(focal_length) == 2:
                    fl_value = focal_length[0] / focal_length[1]
                    hint_text += f"- Focal length: {fl_value:.0f}mm\n"
                else:
                    hint_text += f"- Focal length: {focal_length}mm\n"
            
            if piexif.ImageIFD.GPSTag in exif_ptr:
                gps_info = exif_ptr[piexif.ImageIFD.GPSTag]
                if gps_info:
                    try:
                        lat_ref = gps_info.get(1, 'N')
                        lat_dms = gps_info.get(2, None)
                        lon_ref = gps_info.get(3, 'E')
                        lon_dms = gps_info.get(4, None)
                        
                        if lat_dms and lon_dms:
                            def dms_to_decimal(dms, ref):
                                degrees = dms[0]
                                minutes = dms[1]
                                seconds = dms[2]
                                decimal = degrees + minutes/60 + seconds/3600
                                if ref in ['S', 'W']:
                                    decimal = -decimal
                                return decimal
                            
                            lat_decimal = dms_to_decimal(lat_dms, lat_ref)
                            lon_decimal = dms_to_decimal(lon_dms, lon_ref)
                            #hint_text += f"- GPS coordinates: {lat_decimal:.6f}, {lon_decimal:.6f}\n"
                            
                            try:
                                location = _geocoder.query(lat_decimal,lon_decimal)
                                if location:
                                    hint_text += f"- Location: {location}\n"
                            except Exception as e:
                                # Geocoding failed, but we still have coordinates
                                print(f"Warning: Geocoding failed for coordinates {lat_decimal},{lon_decimal}: {e}")
                                
                    except (KeyError, TypeError, IndexError) as ex:
                        raise ex

            
            return hint_text if hint_text != "EXIF Metadata:\n" else None
            
    except (IOError, OSError) as e:
        print(f"Warning: Failed to read EXIF data from {image_path}: {e}")
        return None
    except Exception as e:
        print(f"Warning: Unexpected error reading EXIF data from {image_path}: {e}")
        return None


### Register hint sources in the following three functions ###

def get_available_hint_sources() -> Dict[str, str]:
    return {
        "full_path": "Full Path Information",
        "metadata": "Directory-level metadata.json",
        "json": "Per-Image .Json",
        "exif": "EXIF Metadata"
        # Display names can be customized here without affecting functionality
    }

def get_hint_source_descriptions() -> Dict[str, str]:
    # For longer UI description
    return {
        "full_path": "Includes the full file path.",
        "metadata": "Reads metadata.json file from image's directory",
        "json": "Reads the [imagename].json file for each image",
        "exif": "Extracts EXIF metadata including GPS reverse lookup"
    }

HINT_FUNCTIONS: Dict[str, Callable] = {
    "full_path": get_full_path_hint,
    "metadata": get_metadata_hint,
    "json": get_json_hint,
    "exif": get_exif_hint
}

def _validate_hint_sources():
    """Verifies  hint code is properly configured with registrations"""
    available_hint_sources_keys = set(get_available_hint_sources().keys())
    hint_source_descriptions_keys = set(get_hint_source_descriptions().keys())
    hint_functions_keys = set(HINT_FUNCTIONS.keys())

    assert available_hint_sources_keys == hint_source_descriptions_keys == hint_functions_keys, "Hint sources not properly registered. Check source code."
