import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as cx

# 1. Define the search area (Greater London)
# We use a slightly wider box to ensure we catch everything, then filter visually.
london_bbox = (-0.55, 51.25, 0.35, 51.70) 

print("Scouting for substations... this may take 30-60 seconds.")

# 2. The "Lightweight" Pull
# We use the 'columns' argument to IGNORE the heavy energy data.
# We only want to know WHO exists and WHERE they are.
df_locations = gpd.read_parquet(
    "s3://weave.energy/smart-meter",
    bbox=london_bbox,
    columns=['secondary_substation_unique_id', 'geometry'], # <-- The secret sauce
    storage_options={"anon": True}
)

# 3. Clean up duplicates
# The raw file has one row per timestamp. We only need one row per Substation.
unique_sites = df_locations.drop_duplicates(subset=['secondary_substation_unique_id'])

print(f"Found {len(unique_sites)} unique substations in London.")

# 4. Save the list for your manual review
unique_sites.to_csv("london_substation_candidates.csv", index=False)
print("Saved candidate list to 'london_substation_candidates.csv'")

# 5. Plot them all so you can choose
# We convert to Web Mercator for the background map
sites_map = unique_sites.to_crs(epsg=3857)

fig, ax = plt.subplots(figsize=(12, 12))
sites_map.plot(ax=ax, color='blue', markersize=10, alpha=0.5, label='Candidate Substations')

# Add context map (Street view helps identify residential areas)
cx.add_basemap(ax, source=cx.providers.CartoDB.Positron)

plt.title("Candidate Substations in London")
plt.show()