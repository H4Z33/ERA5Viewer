import os
import xarray as xr
import pandas as pd
import numpy as np
from pathlib import Path
import sqlite3
import re
import logging
import json
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("preprocess")

DATA_DIR = Path(".")
DB_PATH = DATA_DIR / "era5_stats.db"
ERA5_TAM_DIR = DATA_DIR / "era5_land_tamaulipas"
ZARR_PATH = DATA_DIR / "era5_land_tamaulipas.zarr"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS files (
                filename TEXT PRIMARY KEY,
                mtime REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS hourly_stats (
                filename TEXT,
                variable TEXT,
                time_str TEXT,
                mean REAL,
                min REAL,
                max REAL,
                PRIMARY KEY (filename, variable, time_str)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS global_stats (
                collection_id TEXT,
                variable TEXT,
                min REAL,
                max REAL,
                units TEXT,
                long_name TEXT,
                PRIMARY KEY (collection_id, variable)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_time ON hourly_stats(time_str)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_var ON hourly_stats(variable)")

def index_file(path: Path):
    try:
        logger.info(f"Indexing {path.name}...")
        with xr.open_dataset(path, engine="netcdf4") as ds:
            time_dim = next((d for d in ["time", "valid_time"] if d in ds.coords), None)
            lat_dim = next((d for d in ["latitude", "lat"] if d in ds.coords), None)
            lon_dim = next((d for d in ["longitude", "lon"] if d in ds.coords), None)
            
            if not all([time_dim, lat_dim, lon_dim]):
                logger.warning(f"Skipping {path.name}: Missing dimensions.")
                return

            stats_batch = []
            global_batch = []
            
            for v in ds.data_vars:
                if time_dim in ds[v].dims and lat_dim in ds[v].dims and lon_dim in ds[v].dims:
                    # Calculate stats
                    res = ds[v].mean(dim=[lat_dim, lon_dim]).compute()
                    mins = ds[v].min(dim=[lat_dim, lon_dim]).compute()
                    maxs = ds[v].max(dim=[lat_dim, lon_dim]).compute()
                    times = pd.to_datetime(ds[time_dim].values)
                    
                    for i in range(len(times)):
                        stats_batch.append((path.name, v, times[i].isoformat(), float(res.values[i]), float(mins.values[i]), float(maxs.values[i])))
                    
                    # Global Metadata
                    v_min, v_max = float(mins.min()), float(maxs.max())
                    units = ds[v].attrs.get("units", "")
                    long_name = ds[v].attrs.get("long_name", v)
                    
                    match = re.match(r"^(.+?)_\d{4}_\d{2}\.nc$", path.name)
                    cid = match.group(1) if match else path.name
                    global_batch.append((cid, v, v_min, v_max, units, long_name))

            with sqlite3.connect(DB_PATH) as conn:
                if stats_batch:
                    conn.executemany("INSERT OR REPLACE INTO hourly_stats (filename, variable, time_str, mean, min, max) VALUES (?, ?, ?, ?, ?, ?)", stats_batch)
                if global_batch:
                    conn.executemany("INSERT OR REPLACE INTO global_stats (collection_id, variable, min, max, units, long_name) VALUES (?, ?, ?, ?, ?, ?)", global_batch)
                conn.execute("INSERT OR REPLACE INTO files (filename, mtime) VALUES (?, ?)", (path.name, path.stat().st_mtime))
            
            logger.info(f"Successfully indexed {path.name}.")
    except Exception as e:
        logger.error(f"Error indexing {path.name}: {e}")

def consolidate_to_zarr(collection_id: str):
    logger.info(f"Consolidating {collection_id} to Zarr...")
    nc_files = sorted(list(ERA5_TAM_DIR.glob("*.nc")))
    if not nc_files:
        logger.warning("No files found to consolidate.")
        return

    try:
        # Open all files as a single dataset
        ds = xr.open_mfdataset(nc_files, combine='by_coords', engine="netcdf4")
        
        # Optimize for time-series access by chunking along time
        # 1 year of hourly data is ~8760 steps. Chunking by 500-1000 is usually good for performance.
        ds = ds.chunk({"time": 500, "latitude": -1, "longitude": -1})
        
        logger.info(f"Writing to {ZARR_PATH}...")
        ds.to_zarr(ZARR_PATH, mode='w', consolidated=True)
        logger.info("Zarr consolidation complete.")
    except Exception as e:
        logger.error(f"Failed to consolidate to Zarr: {e}")

def main():
    init_db()
    
    # 1. Scan for files
    all_nc = list(DATA_DIR.glob("*.nc"))
    if ERA5_TAM_DIR.exists():
        all_nc.extend(list(ERA5_TAM_DIR.glob("*.nc")))
    
    # 2. Filter updated or new files
    to_index = []
    with sqlite3.connect(DB_PATH) as conn:
        for path in all_nc:
            if "extracted" in str(path): continue
            res = conn.execute("SELECT mtime FROM files WHERE filename = ?", (path.name,)).fetchone()
            if res is None or path.stat().st_mtime > res[0]:
                to_index.append(path)

    if not to_index:
        logger.info("All files are up to-date.")
    else:
        logger.info(f"Found {len(to_index)} files to index.")
        for p in to_index:
            index_file(p)

    # 3. Optional Zarr Consolidation
    # If the Zarr store doesn't exist or we just indexed new files, suggest consolidation
    if not ZARR_PATH.exists() or to_index:
        choice = input("\nDo you want to consolidate NetCDF files into a high-performance Zarr store? (y/n): ")
        if choice.lower() == 'y':
            consolidate_to_zarr("era5_land_tamaulipas")

if __name__ == "__main__":
    main()
