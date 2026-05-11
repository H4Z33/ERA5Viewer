import cdsapi
from pathlib import Path
import json

c = cdsapi.Client()

# Carpeta donde se guardarán los datos
output_dir = Path("era5_land_tamaulipas")
output_dir.mkdir(exist_ok=True)

# Archivo de log
log_file = output_dir / "download_log.json"

# Cargar log existente o crear uno nuevo
if log_file.exists():
    with open(log_file, "r") as f:
        download_log = json.load(f)
else:
    download_log = {}

# Años y meses
years = list(range(1998, 2026))
months = [f"{m:02d}" for m in range(1, 13)]

# Variables deseadas
variables = [
    '2m_temperature',
    'volumetric_soil_water_layer_1',
    'potential_evaporation',
]

# Área geográfica: sur de Tamaulipas
area = [24.0, -99.0, 22.0, -97.0]  # [Norte, Oeste, Sur, Este]

for year in years:
    for month in months:
        target_file = output_dir / f"era5_land_tamaulipas_{year}_{month}.nc"
        key = f"{year}_{month}"

        # Saltar si ya se descargó exitosamente
        if download_log.get(key) == "done" and target_file.exists():
            print(f"[{key}] Ya descargado, saltando.")
            continue

        print(f"[{key}] Descargando ERA5-Land ...")
        try:
            c.retrieve(
                'reanalysis-era5-land',
                {
                    'variable': variables,
                    'year': str(year),
                    'month': month,
                    'day': [f"{d:02d}" for d in range(1, 32)],
                    'time': [f"{h:02d}:00" for h in range(24)],
                    'area': area,
                    'format': 'netcdf',
                },
                str(target_file)
            )
            download_log[key] = "done"
            print(f"[{key}] Descarga completada")
        except Exception as e:
            download_log[key] = f"failed: {str(e)}"
            print(f"[{key}] ERROR: {e}")

        # Guardar log después de cada intento
        with open(log_file, "w") as f:
            json.dump(download_log, f, indent=2)

print("📦 Todas las descargas procesadas. Revisa el log para errores.")
