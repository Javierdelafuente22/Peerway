import pandas as pd
import geopandas as gpd

# 1. Your Curated List of 15 Residential Substations
my_selected_ids = [
    "SSEN-7991001005", "SSEN-8079001005", "SSEN-8103001005",
    "SSEN-8184001005", "SSEN-8184001020", "SSEN-7900001010",
    "SSEN-7900004087", "SSEN-8034001010", "SSEN-2518012120",
    "SSEN-2503607020", "SSEN-2506608140", "SSEN-2522012150",
    "SSEN-2509015020", "SSEN-2521012110", "SSEN-2803012140"
]

print(f"Pulling full available history for {len(my_selected_ids)} selected substations...")

# 2. The Targeted Pull
# Filters now ONLY contain the substation IDs (Temporal filters deleted)
df_energy = gpd.read_parquet(
    "s3://weave.energy/smart-meter",
    filters=[
        ("secondary_substation_unique_id", "in", my_selected_ids)
    ],
    storage_options={"anon": True}
)

# 3. Processing: Pivot & Resample
# Pivot the data so each substation has its own column
timeseries = df_energy.pivot_table(
    index="data_collection_log_timestamp", 
    columns="secondary_substation_unique_id", 
    values="total_consumption_active_import",
    aggfunc='sum'
)

# Ensure the index is datetime for resampling
timeseries.index = pd.to_datetime(timeseries.index)

# Resample to Hourly (Linear interpolation deleted)
# This will calculate the average consumption per hour
hourly_clean = timeseries.resample('h').mean()

# 4. Save Final Dataset
output_filename = "london_15_curated_profiles_full_history.csv"
hourly_clean.to_csv(output_filename)

print(f"Success. Dataset saved to '{output_filename}'.")
print(f"Total rows pulled: {len(hourly_clean)}")
print(hourly_clean.head())