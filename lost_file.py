import os
import cdsapi

c = cdsapi.Client()

year = "2014"
month = "12"

variables = [
    '2m_temperature',
    'volumetric_soil_water_layer_1',
    'potential_evaporation',
]

area = [24.0, -99.0, 22.0, -97.0]  # [Norte, Oeste, Sur, Este]

target_file = f"C:/ERA5_LAND/lostfile/era5_land_tamaulipas_{year}_{month}/data_0.nc"

# Ensure parent directory exists
os.makedirs(os.path.dirname(target_file), exist_ok=True)

c.retrieve(
    'reanalysis-era5-land',
    {
        'variable': variables,
        'year': year,
        'month': month,
        'day': [f"{d:02d}" for d in range(1, 32)],
        'time': [f"{h:02d}:00" for h in range(24)],
        'area': area,
        'format': 'netcdf',
    },
    target_file
)

print("Listo: archivo 2014-12 descargado nuevamente.")
