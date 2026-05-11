import json
from pathlib import Path

log_path = Path("era5_land_tamaulipas/download_log.json")

if not log_path.exists():
    print("Error: download_log.json not found.")
    exit(1)

with open(log_path, "r") as f:
    log = json.load(f)

# Identification
failed_entries = [k for k, v in log.items() if v.startswith("failed")]
data_lag_entries = [k for k in failed_entries if "2025_11" in k or "2025_12" in k]
network_failed_entries = [k for k in failed_entries if k not in data_lag_entries]

print(f"Found {len(failed_entries)} total failed entries.")
print(f"Network failures to retry: {network_failed_entries}")
print(f"Data lag entries (skipping for now): {data_lag_entries}")

# Removal of network failures to allow retry
for key in network_failed_entries:
    del log[key]

with open(log_path, "w") as f:
    json.dump(log, f, indent=2)

print(f"Successfully cleaned {len(network_failed_entries)} network failures from log.")
print("You can now run 'uv run era5_land.py' to retry these downloads.")
