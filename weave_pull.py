import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as cx

# 1. Configuration
london_bbox = (-0.51, 51.28, 0.33, 51.69)

# 2. Data Filtering
# We use 'filters' to ensure we only pull the 2023-2024 window
df = gpd.read_parquet(
    "s3://weave.energy/smart-meter",
    bbox=london_bbox,
    storage_options={"anon": True}
)

# 3. Selection
# Get 15 unique substation IDs found in this specific area/time
unique_profiles = df['secondary_substation_unique_id'].unique()[:15]
filtered_df = df[df['secondary_substation_unique_id'].isin(unique_profiles)]

# 4. Resample to Hourly
# Pivot the data: Rows = Time, Columns = Substation IDs
timeseries = filtered_df.pivot_table(
    index="data_collection_log_timestamp", 
    columns="secondary_substation_unique_id", 
    values="total_consumption_active_import",
    aggfunc='sum'
)

# Ensure the index is datetime and resample to hourly (mean consumption)
timeseries.index = pd.to_datetime(timeseries.index)
hourly_profiles = timeseries.resample('h').mean()

# Save to CSV
hourly_profiles.to_csv("weave_2024_26.csv")
print(hourly_profiles.head())

# 5. Mapping the 15 Substations
def plot_substation_map(data, profile_ids):
    # Filter original data for just the 15 unique locations
    # We drop duplicates so we only have 1 point per substation ID
    geo_data = data[data['secondary_substation_unique_id'].isin(profile_ids)].drop_duplicates('secondary_substation_unique_id')
    
    # Ensure it's in Web Mercator (EPSG:3857) for the background map to align
    geo_data = geo_data.to_crs(epsg=3857)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot the substation points
    geo_data.plot(ax=ax, color='red', markersize=50, edgecolor='white', label='Substations', zorder=5)
    
    # Add the London base map
    cx.add_basemap(ax, source=cx.providers.CartoDB.Positron)
    
    plt.title(f"Location of 15 Selected Substations (London)", fontsize=15)
    plt.legend()
    plt.tight_layout()
    plt.show()

# Run the mapping function
plot_substation_map(df, unique_profiles)