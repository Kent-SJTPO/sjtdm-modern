import geopandas as gpd
from pathlib import Path

# === File Paths ===
taz_path = Path(r"J:\TAZ_Adustment\Input\2010GIS\SJTDM Final TAZ_Nov2011.shp")
cbg_path = Path(r"J:\TAZ_Adustment\Input\2020GIS\tl_2022_34_bg.shp")
output_path = Path(r"J:\TAZ_Adustment\Output\2020TAZsV5_with_centroids.shp")

# === Load Files ===
print("🔄 Loading TAZ and CBG files...")
taz = gpd.read_file(taz_path)
cbg = gpd.read_file(cbg_path)

# === Project to NJ State Plane (ft) ===
if taz.crs.is_geographic:
    taz = taz.to_crs(epsg=6539)
if cbg.crs.is_geographic:
    cbg = cbg.to_crs(epsg=6539)

# === Step 1: Intersect 2010 TAZs with 2020 Block Groups ===
print("📐 Performing spatial intersection...")
intersect = gpd.overlay(taz[['TAZ_112011', 'geometry']], cbg[['GEOID', 'geometry']], how='intersection')

# === Step 2: Process GEOIDs ===
intersect["GEOID2020"] = intersect["GEOID"].str[-7:]      # Keep only block group portion
intersect["GEOID5"] = intersect["GEOID2020"].str[:5]       # First 5 digits

# === Step 3: Merge on TAZ + GEOID5 ===
print("🔁 Dissolving by TAZ_112011 and GEOID5...")
intersect["TAZ_GEOID5"] = intersect["TAZ_112011"].astype(str) + "_" + intersect["GEOID5"]
dissolved = intersect.dissolve(by="TAZ_GEOID5", as_index=False)

# === Step 4: Restore fields ===
dissolved["TAZ_112011"] = dissolved["TAZ_112011"]
dissolved["GEOID5"] = dissolved["GEOID5"]
dissolved["GEOID2020"] = dissolved["GEOID2020"]
dissolved = dissolved.drop(columns=["TAZ_GEOID5"])

# === Step 5: Add original TAZ area, new polygon area, and centroid distance ===
print("➕ Adding acreage and centroid distance info...")
taz["TAZ_area_acres"] = taz.geometry.area / 43560
taz["TAZ_centroid"] = taz.geometry.centroid

# Merge original area/centroid into new geometry
dissolved = dissolved.merge(taz[['TAZ_112011', 'TAZ_area_acres', 'TAZ_centroid']], on='TAZ_112011', how='left')

# Add new polygon area in acres
dissolved["poly_area_acres"] = dissolved.geometry.area / 43560

# Calculate centroid distance (ft)
dissolved["new_centroid"] = dissolved.geometry.centroid
dissolved["centroid_dist_ft"] = dissolved.apply(
    lambda row: row["new_centroid"].distance(row["TAZ_centroid"]), axis=1
)

# Cleanup
dissolved = dissolved.drop(columns=["TAZ_centroid", "new_centroid"])

# === Step 6: Save output ===
print(f"💾 Saving output to {output_path}")
dissolved.to_file(output_path)

print("✅ Done! Output includes original area, new area, and centroid shift.")
