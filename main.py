from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, Response
import xarray as xr
import os
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import re
import logging
import sqlite3
import threading
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("era5-viewer")

app = FastAPI(title="ERA5 Data Viewer")

DATA_DIR = Path(".")
ERA5_TAM_DIR = DATA_DIR / "era5_land_tamaulipas"
ERA5_TAM_ZARR = DATA_DIR / "era5_land_tamaulipas.zarr"
DB_PATH = DATA_DIR / "era5_stats.db"
MANIFEST_PATH = DATA_DIR / "datasets_manifest.json"

class StatsDB:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
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

    def get_file_mtime(self, filename: str) -> Optional[float]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                res = conn.execute("SELECT mtime FROM files WHERE filename = ?", (filename,)).fetchone()
                return res[0] if res else None
        except Exception: return None

    def update_file(self, filename: str, mtime: float):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR REPLACE INTO files (filename, mtime) VALUES (?, ?)", (filename, mtime))

    def insert_stats(self, stats: List[tuple]):
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany("INSERT OR REPLACE INTO hourly_stats (filename, variable, time_str, mean, min, max) VALUES (?, ?, ?, ?, ?, ?)", stats)

    def update_global_stats(self, collection_id: str, variable: str, v_min: float, v_max: float, units: str, long_name: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO global_stats (collection_id, variable, min, max, units, long_name)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (collection_id, variable, v_min, v_max, units, long_name))

    def get_collection_stats(self, filenames: List[str], variable: str, start: str = None, end: str = None):
        placeholders = ','.join(['?'] * len(filenames))
        params = filenames + [variable]
        query = f"SELECT time_str, mean, min, max FROM hourly_stats WHERE filename IN ({placeholders}) AND variable = ?"
        if start:
            query += " AND time_str >= ?"
            params.append(start)
        if end:
            query += " AND time_str <= ?"
            params.append(end)
        query += " ORDER BY time_str ASC"
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_all_variable_stats(self, collection_id: str) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            res = conn.execute("SELECT variable, min, max, units, long_name FROM global_stats WHERE collection_id = ?", (collection_id,)).fetchall()
            return {r[0]: {"min": r[1], "max": r[2], "units": r[3], "label": r[4]} for r in res}

class DataManager:
    def __init__(self):
        self.collections: Dict[str, List[Path]] = {}
        self.zarr_collections: Dict[str, Path] = {}
        self.manifest: Dict[str, Any] = {}
        self.dataset_cache: Dict[str, xr.Dataset] = {}
        self.cache_limit = 2
        self.db = StatsDB(DB_PATH)
        self.load_manifest()
        self.scan_datasets()
        # Start background indexing
        threading.Thread(target=self.index_all_files, daemon=True).start()

    def load_manifest(self):
        if MANIFEST_PATH.exists():
            try:
                with open(MANIFEST_PATH, "r") as f:
                    self.manifest = json.load(f)
                logger.info(f"Loaded manifest with {len(self.manifest)} collections.")
            except Exception as e:
                logger.error(f"Failed to load manifest: {e}")

    def scan_datasets(self):
        self.collections = {}
        self.zarr_collections = {}
        if ERA5_TAM_ZARR.exists():
            self.zarr_collections["era5_land_tamaulipas"] = ERA5_TAM_ZARR

        all_nc = list(DATA_DIR.glob("*.nc"))
        if ERA5_TAM_DIR.exists(): all_nc.extend(list(ERA5_TAM_DIR.glob("*.nc")))
        
        for path in all_nc:
            if "extracted" in str(path): continue
            match = re.match(r"^(.+?)_\d{4}_\d{2}\.nc$", path.name)
            if match:
                prefix = match.group(1)
                if prefix in self.zarr_collections: continue
                if prefix not in self.collections: self.collections[prefix] = []
                self.collections[prefix].append(path)
            else: self.collections[path.name] = [path]
        
        for k in self.collections: self.collections[k].sort()

    def index_all_files(self):
        all_nc_paths = [p for paths in self.collections.values() for p in paths]
        for path in all_nc_paths:
            current_mtime = path.stat().st_mtime
            cached_mtime = self.db.get_file_mtime(path.name)
            if cached_mtime is None or current_mtime > cached_mtime:
                self.index_file(path)
                self.db.update_file(path.name, current_mtime)

    def index_file(self, path: Path):
        try:
            with xr.open_dataset(path, engine="netcdf4") as ds:
                time_dim = next((d for d in ["time", "valid_time"] if d in ds.coords), None)
                lat_dim = next((d for d in ["latitude", "lat"] if d in ds.coords), None)
                lon_dim = next((d for d in ["longitude", "lon"] if d in ds.coords), None)
                if not all([time_dim, lat_dim, lon_dim]): return
                stats_batch = []
                for v in ds.data_vars:
                    if time_dim in ds[v].dims and lat_dim in ds[v].dims and lon_dim in ds[v].dims:
                        # Slice-level stats
                        res = ds[v].mean(dim=[lat_dim, lon_dim]).compute()
                        mins = ds[v].min(dim=[lat_dim, lon_dim]).compute()
                        maxs = ds[v].max(dim=[lat_dim, lon_dim]).compute()
                        times = pd.to_datetime(ds[time_dim].values)
                        for i in range(len(times)):
                            stats_batch.append((path.name, v, times[i].isoformat(), float(res.values[i]), float(mins.values[i]), float(maxs.values[i])))
                        
                        # Global metadata for this file/collection
                        v_min, v_max = float(mins.min()), float(maxs.max())
                        units = ds[v].attrs.get("units", "")
                        long_name = ds[v].attrs.get("long_name", v)
                        
                        # Use file prefix as collection ID for global stats
                        match = re.match(r"^(.+?)_\d{4}_\d{2}\.nc$", path.name)
                        cid = match.group(1) if match else path.name
                        self.db.update_global_stats(cid, v, v_min, v_max, units, long_name)

                if stats_batch: self.db.insert_stats(stats_batch)
        except Exception as e: logger.error(f"Failed to index {path.name}: {e}")

    def get_dataset(self, collection_id: str, granularity: str = "original", start_date: str = None, end_date: str = None) -> xr.Dataset:
        cache_key = f"{collection_id}_{granularity}_{start_date}_{end_date}"
        if cache_key in self.dataset_cache: return self.dataset_cache[cache_key]
        if len(self.dataset_cache) >= self.cache_limit: self.dataset_cache.clear()

        try:
            if collection_id in self.zarr_collections:
                ds = xr.open_zarr(self.zarr_collections[collection_id], consolidated=True)
            elif collection_id in self.collections:
                ds = xr.open_mfdataset(self.collections[collection_id], combine='by_coords', engine="netcdf4", chunks={"time": 24*31})
            else: raise HTTPException(status_code=404, detail="Collection not found")
            
            time_dim = next((d for d in ["time", "valid_time"] if d in ds.coords), None)
            if time_dim:
                if start_date or end_date:
                    s = start_date if start_date else ds[time_dim].values[0]
                    e = end_date if end_date else ds[time_dim].values[-1]
                    ds = ds.sel({time_dim: slice(s, e)})
                if granularity != "original":
                    freq_map = {"daily": "1D", "monthly": "1MS", "quarterly": "QE", "semester": "6ME", "yearly": "YE"}
                    freq = freq_map.get(granularity)
                    if freq: ds = ds.resample({time_dim: freq}).mean()
            self.dataset_cache[cache_key] = ds
            return ds
        except Exception as e: raise HTTPException(status_code=500, detail=f"Error processing dataset: {str(e)}")

    def get_layers(self) -> List[Dict[str, Any]]:
        layers = []
        # Use manifest for faster naming/metadata
        for cid in sorted(self.manifest.keys()):
            layers.append({"id": cid, "name": self.manifest[cid]["name"]})
        # Add everything else
        all_ids = set(self.zarr_collections.keys()) | set(self.collections.keys())
        for cid in sorted(all_ids):
            if cid in self.manifest: continue
            layers.append({"id": cid, "name": f"{cid.replace('_', ' ').title()}"})
        return layers

    def get_metadata(self, collection_id: str, granularity: str = "original", start_date: str = None, end_date: str = None):
        # Optimization: Return manifest instantly if no date/granularity filters are applied
        if collection_id in self.manifest and granularity == "original" and not (start_date or end_date):
            return self.manifest[collection_id]

        # Try DB global stats first
        db_stats = self.db.get_all_variable_stats(collection_id)
        
        ds = self.get_dataset(collection_id, granularity, start_date, end_date)
        lat_dim = next((d for d in ["latitude", "lat"] if d in ds.coords), None)
        lon_dim = next((d for d in ["longitude", "lon"] if d in ds.coords), None)
        time_dim = next((d for d in ["time", "valid_time"] if d in ds.coords), None)
        lat, lon = ds[lat_dim].values, ds[lon_dim].values
        times_raw = ds[time_dim].values
        times = [pd.to_datetime(t, errors='coerce').strftime('%Y-%m-%d %H:%M') for t in times_raw]
        
        display_vars = {}
        for v in ds.data_vars:
            if lat_dim in ds[v].dims and lon_dim in ds[v].dims and time_dim in ds[v].dims:
                if v in db_stats and granularity == "original":
                    v_min, v_max = db_stats[v]["min"], db_stats[v]["max"]
                    units, label = db_stats[v]["units"], db_stats[v]["label"]
                else:
                    # Fallback to computation if not in DB or if resampled
                    v_min, v_max = float(ds[v].min().compute()), float(ds[v].max().compute())
                    units, label = ds[v].attrs.get("units", ""), ds[v].attrs.get("long_name", v)
                
                if v == "t2m" and units == "K": v_min, v_max, units = v_min-273.15, v_max-273.15, "°C"
                display_vars[v] = {"label": label, "min": v_min, "max": v_max, "units": units, "description": label}
        
        return {"bounds": {"lat": [float(lat.min()), float(lat.max())], "lon": [float(lon.min()), float(lon.max())]},
                "shape": {"lat": len(lat), "lon": len(lon)}, "times": times, "variables": display_vars,
                "range": {"start": times[0].split(' ')[0], "end": times[-1].split(' ')[0]},
                "latest_idx": len(times) - 1, "dims": {"lat": lat_dim, "lon": lon_dim, "time": time_dim}}

    def get_slice(self, collection_id: str, variable: str, time_idx: int, granularity: str = "original", start_date: str = None, end_date: str = None):
        ds = self.get_dataset(collection_id, granularity, start_date, end_date)
        time_dim = next((d for d in ["time", "valid_time"] if d in ds.coords), None)
        data_var = ds[variable]
        if "expver" in data_var.dims: data_var = data_var.sel(expver=1) if data_var.expver.size > 1 else data_var.isel(expver=0)
        total_steps = len(ds[time_dim]); safe_idx = max(0, min(time_idx, total_steps - 1))
        data_slice_raw = data_var.isel({time_dim: safe_idx}).compute().values
        units = ds[variable].attrs.get("units", "")
        if variable == "t2m" and units == "K": data_slice_raw, units = data_slice_raw-273.15, "°C"
        return {"data": np.where(np.isnan(data_slice_raw), None, data_slice_raw).tolist(), "min": float(np.nanmin(data_slice_raw)), "max": float(np.nanmax(data_slice_raw)), "units": units}

data_manager = DataManager()

@app.get("/api/layers")
async def get_layers(): return data_manager.get_layers()

@app.get("/api/metadata/{collection_id}")
async def get_metadata(collection_id: str, granularity: str = "original", start: Optional[str] = None, end: Optional[str] = None):
    return data_manager.get_metadata(collection_id, granularity, start, end)

@app.get("/api/data/{collection_id}/{variable}/{time_idx}")
async def get_data(collection_id: str, variable: str, time_idx: int, granularity: str = "original", start: Optional[str] = None, end: Optional[str] = None):
    return data_manager.get_slice(collection_id, variable, time_idx, granularity, start, end)

@app.get("/api/analytics/{collection_id}/{variable}")
async def get_analytics(collection_id: str, variable: str, granularity: str = "original", start: Optional[str] = None, end: Optional[str] = None):
    import matplotlib.dates as mdates
    
    means, mins, maxs, times = None, None, None, None
    units = ""
    
    # Path 1: Try DB Cache (Fast)
    if granularity == "original" and collection_id in data_manager.collections:
        filenames = [p.name for p in data_manager.collections[collection_id]]
        stats_df = data_manager.db.get_collection_stats(filenames, variable, start, end)
        if not stats_df.empty:
            times = pd.to_datetime(stats_df['time_str'])
            means, mins, maxs = stats_df['mean'].values, stats_df['min'].values, stats_df['max'].values
            units = "K" if variable == "t2m" else ""
            if variable == "t2m": means, mins, maxs, units = means-273.15, mins-273.15, maxs-273.15, "°C"

    # Path 2: Fallback to Computation (Slow but Accurate for Resampled/Zarr)
    if means is None:
        ds = data_manager.get_dataset(collection_id, granularity, start, end)
        metadata = data_manager.get_metadata(collection_id, granularity, start, end)
        time_dim, lat_dim, lon_dim = metadata["dims"]["time"], metadata["dims"]["lat"], metadata["dims"]["lon"]
        data_var = ds[variable]
        if "expver" in data_var.dims: data_var = data_var.sel(expver=1) if data_var.expver.size > 1 else data_var.isel(expver=0)
        
        means = data_var.mean(dim=[lat_dim, lon_dim]).compute().values
        mins = data_var.min(dim=[lat_dim, lon_dim]).compute().values
        maxs = data_var.max(dim=[lat_dim, lon_dim]).compute().values
        times = pd.to_datetime(ds[time_dim].values)
        units = ds[variable].attrs.get("units", "")
        if variable == "t2m" and units == "K": means, mins, maxs, units = means-273.15, mins-273.15, maxs-273.15, "°C"

    # Common Plotting Logic
    long_name = variable
    if collection_id in data_manager.manifest:
        vars_info = data_manager.manifest[collection_id].get("variables", {})
        if variable in vars_info: long_name = vars_info[variable].get("label", variable)

    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [2, 1]})
    fig.patch.set_facecolor('#0f172a'); [ax.set_facecolor('#1e293b') for ax in [ax1, ax2]]
    
    # 1. Main Trend Line
    ax1.fill_between(times, mins, maxs, color='#3a7eb8', alpha=0.3)
    sns.lineplot(x=times, y=means, ax=ax1, color='#ef4444', linewidth=2)
    
    # Date axis formatting
    ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(ax1.get_xticklabels(), rotation=30, ha='right', fontsize=8)

    ax1.set_title(f"Temporal Trend: {long_name}", fontsize=12, pad=10, fontweight='bold')
    ax1.set_ylabel(f"Value ({units})", fontsize=9)
    ax1.set_xlabel("") # Remove "None" / label
    ax1.grid(True, alpha=0.1)

    # 2. Spatial Distribution (Histogram)
    try:
        ds_sample = data_manager.get_dataset(collection_id)
        time_dim_s = next((d for d in ["time", "valid_time"] if d in ds_sample.coords), "time")
        dist_data = ds_sample[variable].mean(dim=time_dim_s).compute().values.flatten()
        dist_data = dist_data[~np.isnan(dist_data)]
        if variable == "t2m": dist_data = dist_data - 273.15
        sns.histplot(dist_data, ax=ax2, color='#38bdf8', kde=True, bins=30)
        ax2.set_title(f"Spatial Distribution: {long_name}", fontsize=10, pad=8)
        ax2.set_xlabel("") # Remove label
    except Exception as e:
        ax2.text(0.5, 0.5, f"Distribution Not Available", ha='center', va='center', color='gray')

    plt.tight_layout(pad=4.0); buf = io.BytesIO(); plt.savefig(buf, format='png', dpi=110); plt.close(fig); buf.seek(0)
    return Response(content=buf.getvalue(), media_type="image/png")

@app.get("/api/timeline/{collection_id}/{variable}")
async def get_timeline_data(collection_id: str, variable: str, granularity: str = "original", start: Optional[str] = None, end: Optional[str] = None):
    # Fetch data from DB for the waveform
    if collection_id in data_manager.collections:
        filenames = [p.name for p in data_manager.collections[collection_id]]
        stats_df = data_manager.db.get_collection_stats(filenames, variable, start, end)
        if not stats_df.empty:
            # Normalize means for easier drawing on client side
            means = stats_df['mean'].values
            if variable == "t2m": means = means - 273.15
            
            # Simple normalization to 0-1 range for the waveform
            m_min, m_max = np.nanmin(means), np.nanmax(means)
            norm_means = ((means - m_min) / (m_max - m_min)) if m_max > m_min else np.zeros_like(means)
            
            return {
                "times": stats_df['time_str'].tolist(),
                "means": norm_means.tolist(),
                "actual_means": means.tolist(),
                "units": "°C" if variable == "t2m" else ""
            }
    return {"times": [], "means": []}

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8008, reload=True)
