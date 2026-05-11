import json
from pathlib import Path

log_path = Path("era5_land_tamaulipas/download_log.json")

if not log_path.exists():
    print("Error: download_log.json not found.")
    exit(1)

with open(log_path, "r") as f:
    log = json.load(f)

# The 12 months that were cleared
missing_months = [
    '2003_01', '2007_07', '2008_02', '2008_04', '2011_04', 
    '2016_02', '2017_04', '2020_09', '2022_12', '2023_01', 
    '2024_07', '2024_10'
]

# Restore them as "failed (retry pending)"
for month in missing_months:
    if month not in log:
        log[month] = "failed: (retry pending - awaiting credentials)"

# Sort the log keys for better readability if possible (optional)
sorted_keys = sorted(log.keys(), key=lambda x: (int(x.split('_')[0]), int(x.split('_')[1])))
new_log = {k: log[k] for k in sorted_keys}

with open(log_path, "w") as f:
    json.dump(new_log, f, indent=2)

print(f"Successfully restored {len(missing_months)} failed entries to the log.")
