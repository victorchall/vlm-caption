"""
Reverse GPS lookup module.

This module provides efficient reverse geocoding using a KD-Tree data structure
for fast nearest neighbor lookups on GPS coordinates.  Database is cached for 
lifecycle of application.

Location is a local name or landmark.
Admin1zone is the state, province, prefecture, etc., depending on country's first administrative heirarchy.

Usage:
    from hints.gps import LocalGeocoder
    geocoder = LocalGeocoder("custom_data.tsv")
    location, admin1zone, country = geocoder.query(47.0755, -9.3063)
"""

from .local_geocoder import LocalGeocoder

__all__ = [
    'LocalGeocoder'
]
