import geopandas as gpd
import pandas as pd

# File paths
taz_path = r"J:\TAZ_Adustment\Input\2010GIS\SJTDM Final TAZ_Nov2011.shp"
bg_path = r"J:\TAZ_Adustment\Input\2020GIS\tl_2022_34_bg.shp"
output_path = r"J:\TAZ_Adustment\Output\adjusted_taz_by_bg.geojson"

print("🔄 Loading TAZ shapefile...")
taz_gdf = gpd.read_file(taz_path)

print("🔄 Loading 2020 Census Block Groups...")
bg_gdf = gpd.read_file(bg_path)

# Ensure both datasets use the same CRS
if taz_gdf.crs != bg_gdf.crs:
    print("♻️ Reprojecting Block Groups to match TAZ CRS...")
    bg_gdf = bg_gdf.to_crs(taz_gdf.crs)

# Spatial join: assign each block group to the TAZ it intersects the most
print("🔗 Performing spatial overlay...")
intersection = gpd.overlay(bg_gdf, taz_gdf[['TRACT2010', 'geometry']], how='intersection')

# Calculate area of each intersected piece
intersection['area'] = intersection.geometry.area

# Get the largest intersecting TAZ for each block group
print("🧮 Assigning Block Groups to dominant TAZs...")
idx = intersection.groupby('GEOID')['area'].idxmax()
dominant_join = intersection.loc[idx, ['GEOID', 'TRACT2010']]

# Merge assignments back to original BG file
bg_gdf = bg_gdf.merge(dominant_join, on='GEOID', how='left')

# Save result
print(f"💾 Saving adjusted output to {output_path}...")
bg_gdf.to_file(output_path, driver='GeoJSON')

print("✅ Adjustment complete.")

