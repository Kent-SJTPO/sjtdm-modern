import geopandas as gpd
from pathlib import Path

# File paths
input_path = Path(r"J:\TAZ_Adustment\Input\2020GIS\Adjusted\adjusted_taz.shp")
output_shp = Path(r"J:\TAZ_Adustment\Output\flagged_split_tazs.shp")
output_csv = Path(r"J:\TAZ_Adustment\Output\flagged_split_tazs.csv")

# Load shapefile
print("🔄 Loading adjusted TAZs...")
gdf = gpd.read_file(input_path)

# Reproject if needed
if gdf.crs.to_epsg() != 3424:
    print("🌐 Reprojecting to EPSG:3424...")
    gdf = gdf.to_crs("EPSG:3424")

# Filter for suspect fragments
print("🔍 Flagging split polygons with large centroid shift...")
flagged = gdf[(gdf["Preserved"] == 0) & (gdf["centroid_s"] > 500)]

# Save results
print(f"💾 Saving shapefile to {output_shp}...")
flagged.to_file(output_shp)

print(f"📄 Saving CSV to {output_csv}...")
flagged.drop(columns="geometry").to_csv(output_csv, index=False)

print("✅ Done. Flagged records exported.")
