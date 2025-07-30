import geopandas as gpd
from shapely.ops import unary_union
from shapely.geometry import LineString
from pathlib import Path
import pandas as pd

# File paths
input_path = Path(r"J:\TAZ_Adustment\Input\2020GIS\Fourth.shp")
output_path = Path(r"J:\TAZ_Adustment\Output\Fourth_merged.shp")

# Load and reproject data
print("🔄 Loading shapefile...")
gdf = gpd.read_file(input_path)
gdf = gdf.to_crs("EPSG:3424")  # Ensure units in feet

# Compute area in acres
gdf["area_acres"] = gdf.geometry.area / 43560

# Split into small and large polygons
small_gdf = gdf[gdf["area_acres"] <= 5].copy()
large_gdf = gdf[gdf["area_acres"] > 5].copy()

# Create spatial index for large polygons
large_sindex = large_gdf.sindex

# Store unmerged small parcels
unmerged = []

print("🔁 Merging small parcels...")
for idx, small_row in small_gdf.iterrows():
    small_geom = small_row.geometry
    geoid = small_row["GEOID2020"]

    # Find candidate neighbors with same GEOID2020
    candidates_idx = list(large_sindex.intersection(small_geom.bounds))
    candidates = large_gdf.iloc[candidates_idx]
    candidates = candidates[candidates["GEOID2020"] == geoid]

    # Find neighbor with longest shared boundary
    max_shared_len = 0
    best_idx = None

    for cidx, candidate in candidates.iterrows():
        shared = small_geom.boundary.intersection(candidate.geometry.boundary)
        if isinstance(shared, LineString):
            shared_len = shared.length
        elif shared.geom_type.startswith("Multi"):
            shared_len = sum(part.length for part in shared.geoms if isinstance(part, LineString))
        else:
            shared_len = 0

        if shared_len > max_shared_len:
            max_shared_len = shared_len
            best_idx = cidx

    if best_idx is not None:
        # Merge small into best match
        best_geom = large_gdf.at[best_idx, "geometry"]
        merged_geom = unary_union([small_geom, best_geom])
        large_gdf.at[best_idx, "geometry"] = merged_geom
    else:
        unmerged.append(small_row)

# Combine results
unmerged_gdf = gpd.GeoDataFrame(unmerged, crs=gdf.crs)
final_gdf = pd.concat([large_gdf, unmerged_gdf], ignore_index=True)

# Save output
print(f"💾 Saving output to {output_path}...")
final_gdf.to_file(output_path)

print("✅ Done merging small parcels.")
