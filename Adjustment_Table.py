import geopandas as gpd
import pandas as pd
from pathlib import Path

# Update these paths to match your local file locations
taz_path = Path(r"J:\TAZ_Adustment\Input\2010GIS\SJTDM Final TAZ_Nov2011.shp")
bg_path = Path(r"J:\TAZ_Adustment\Input\2020GIS\tl_2022_34_bg.shp")
output_csv = Path(r"J:\TAZ_Adustment\Output\TAZ_Relocation_Table.csv")

# Load shapefiles
print("🔄 Loading TAZ shapefile...")
taz_gdf = gpd.read_file(taz_path)

print("🔄 Loading Block Groups shapefile...")
bg_gdf = gpd.read_file(bg_path)

# Reproject to NJ State Plane (EPSG:3424)
print("🧭 Reprojecting to EPSG:3424 for area calculations...")
taz_gdf = taz_gdf.to_crs(epsg=3424)
bg_gdf = bg_gdf.to_crs(epsg=3424)

# Perform spatial overlay
print("🔗 Performing spatial intersection...")
intersection = gpd.overlay(bg_gdf, taz_gdf[['TRACT2010', 'geometry']], how='intersection', keep_geom_type=False)

# Calculate area in square feet
intersection['area_sf'] = intersection.geometry.area
intersection = intersection.rename(columns={'TRACT2010': 'Origin_TAZ'})

# Identify the dominant (largest area) TAZ for each block group
print("🧮 Determining dominant TAZ for each block group...")
intersection_sorted = intersection.sort_values(by='area_sf', ascending=False)
dominant_taz = intersection_sorted.drop_duplicates(subset='GEOID')[['GEOID', 'Origin_TAZ']].rename(columns={'Origin_TAZ': 'Destination_TAZ'})

# Join dominant TAZ info back into full intersection
result = intersection_sorted.merge(dominant_taz, on='GEOID', how='left')

# Select relevant columns and sort
result = result[['GEOID', 'Origin_TAZ', 'Destination_TAZ', 'area_sf']].sort_values(by='area_sf', ascending=False)

# Save to CSV
print(f"💾 Writing results to {output_csv}...")
result.to_csv(output_csv, index=False)

print("✅ Done. Output CSV includes GEOID, Origin_TAZ, Destination_TAZ, and Area (sf).")
