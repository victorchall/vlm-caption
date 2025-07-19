import numpy as np
from sklearn.neighbors import KDTree
import csv
from math import radians, cos, sin
import os
from typing import List, Tuple, Optional

class LocalGeocoder:
    """
    A cached reverse geocoder using KD-Tree for efficient nearest neighbor lookup.
    
    The tree and metadata are built lazily on first query and cached for subsequent calls.
    """
    def __init__(self, tsv_path: str = "hints/gps/extracted_location_data.tsv"):
        """
        Initialize the geocoder with a path to the TSV data file.
        
        Parameters
        ----------
        tsv_path : str
            Path to the tab-delimited file with lat, lon, location_name, admin_zone, country
        """
        self.tsv_path = tsv_path
        self.tree: Optional[KDTree] = None
        self.meta: Optional[List[Tuple[str, str, str]]] = None
        self._initialized = False
    
    def _build_kdtree(self):
        if not os.path.exists(self.tsv_path):
            raise FileNotFoundError(f"Geocoding data file not found: {self.tsv_path}")
        
        vectors = []
        meta = []
        
        print(f"Building KDTree for GPS reverse lookup, this may take 30-60 seconds...")

        with open(self.tsv_path, newline="", encoding="utf-8") as fh:
            reader = csv.reader(fh, delimiter="\t")
            for row in reader:
                if not row:        # skip empty lines
                    continue
                lat, lon = map(float, row[:2])
                location_name, admin_zone, country = row[2:5]

                # Convert (lat, lon) -> unit vector on sphere
                lat_r, lon_r = radians(lat), radians(lon)
                x = cos(lat_r) * cos(lon_r)
                y = cos(lat_r) * sin(lon_r)
                z = sin(lat_r)
                vectors.append((x, y, z))

                meta.append((location_name, admin_zone, country))

        vectors = np.asarray(vectors, dtype=np.float32)
        tree = KDTree(vectors, leaf_size=40, metric="euclidean")
        return tree, meta
    
    def _ensure_initialized(self):
        if not self._initialized:
            self.tree, self.meta = self._build_kdtree()
            self._initialized = True
    
    def query(self, query_lat: float, query_lon: float) -> Tuple[str, str, str]:
        """
        Find the nearest location to the given coordinates.
        
        Parameters
        ----------
        query_lat, query_lon : float
            Query coordinates in degrees
        
        Returns
        -------
        tuple
            (location_name, admin_zone, country) for the nearest neighbor
        """
        self._ensure_initialized()
        
        assert self.tree is not None, "Tree should be initialized"
        assert self.meta is not None, "Meta should be initialized"
        
        q_lat_r, q_lon_r = radians(query_lat), radians(query_lon)
        qx = cos(q_lat_r) * cos(q_lon_r)
        qy = cos(q_lat_r) * sin(q_lon_r)
        qz = sin(q_lat_r)
        query_vec = np.array([[qx, qy, qz]], dtype=np.float32)

        dist, ind = self.tree.query(query_vec, k=1) 
        idx = ind[0][0]
        return self.meta[idx]
