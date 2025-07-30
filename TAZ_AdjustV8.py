import geopandas as gpd
import numpy as np
from pathlib import Path

# === File Paths ===
taz_path = Path(r"J:\TAZ_Adustment\Input\2010GIS\SJTDM Final TAZ_Nov2011.shp")
cbg_path = Path(r"J:\TAZ_Adustment\Input\2020GIS\tl_2022_34_bg.shp")
output_path = Path(r"J:\TAZ_Adustment\Output\2020TAZsV8_with_centroids.shp")
audit_log_path = Path(r"J:\TAZ_Adustment\Output\reassigned_small_parcels.csv")
invalid_geom_path = Path(r"J:\TAZ_Adustment\Output\TAZv8_invalid_geometry.gpkg")

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
intersect = gpd.overlay(
    taz[['TAZ_112011', 'geometry']],
    cbg[['GEOID', 'geometry']],
    how='intersection',
    keep_geom_type=False
)

# === Step 2: Process GEOIDs and Calculate Area ===
intersect["GEOID2020"] = intersect["GEOID"].str[-7:]
intersect["GEOID5"] = intersect["GEOID2020"].str[:5]
intersect["area_acres"] = intersect.geometry.area / 43560
intersect["GEOID2020_int"] = intersect["GEOID2020"].astype(int)

# === Step 3: Reassign Small Parcels by Closest GEOID within ±999 ===
SMALL_PARCEL_ACRES = 0.5
valid_geoids = intersect["GEOID2020_int"].unique()
valid_array = np.array(valid_geoids)

def find_closest_geoid(val, candidates, threshold=999):
    diffs = abs(candidates - val)
    min_diff = diffs.min()
    if min_diff < threshold:
        return candidates[diffs.argmin()]
    else:
        return val

print("🔍 Reassigning small parcels by closest GEOID...")
small = intersect["area_acres"] < SMALL_PARCEL_ACRES
intersect.loc[small, "GEOID2020_int"] = intersect.loc[small, "GEOID2020_int"].apply(
    lambda x: find_closest_geoid(x, valid_array, threshold=999)
)

# Post-check
unmatched = intersect.loc[small]
still_unmatched = ~unmatched["GEOID2020_int"].isin(valid_geoids)
print(f"⚠️ {still_unmatched.sum()} small parcels still unmatched after ±999 threshold")

# Audit log (optional)
intersect.loc[small, ["TAZ_112011", "GEOID", "GEOID2020_int", "area_acres"]].to_csv(
    audit_log_path, index=False
)

# Convert to final GEOID string
intersect["final_GEOID2020"] = intersect["GEOID2020_int"].astype(str)

# === Step 4: Dissolve by TAZ and reassigned GEOID ===
print("🔁 Dissolving by TAZ_112011 and GEOID5...")
intersect["TAZ_GEOID5"] = intersect["TAZ_112011"].astype(str) + "_" + intersect["final_GEOID2020"].str[:5]
dissolved = intersect.dissolve(by="TAZ_GEOID5", as_index=False)

# === Step 5: Restore fields ===
dissolved["TAZ_112011"] = dissolved["TAZ_112011"]
dissolved["GEOID5"] = dissolved["final_GEOID2020"].str[:5]
dissolved["GEOID2020"] = dissolved["final_GEOID2020"]

# === Step 6: Add area and centroid shift info ===
print("➕ Adding acreage and centroid distance info...")
taz["TAZ_area_acres"] = taz.geometry.area / 43560
taz["TAZ_centroid"] = taz.geometry.centroid

# Merge original area and centroid
dissolved = dissolved.merge(
    taz[['TAZ_112011', 'TAZ_area_acres', 'TAZ_centroid']],
    on='TAZ_112011',
    how='left'
)

dissolved["poly_area_acres"] = dissolved.geometry.area / 43560
dissolved["new_centroid"] = dissolved.geometry.centroid
dissolved["centroid_dist_ft"] = dissolved.apply(
    lambda row: row["new_centroid"].distance(row["TAZ_centroid"]), axis=1
)

# Final cleanup
dissolved = dissolved.drop(columns=[
    "TAZ_centroid", "new_centroid", "TAZ_GEOID5", "final_GEOID2020"
])

# === Step 7A: Filter invalid geometry types for Shapefile
print("🧼 Filtering unsupported geometries for Shapefile output...")
valid_types = ["Polygon", "MultiPolygon"]
invalid = dissolved[~dissolved.geometry.type.isin(valid_types)]

if not invalid.empty:
    invalid.to_file(invalid_geom_path, driver="GPKG")
    print(f"⚠️ {len(invalid)} invalid geometries saved to {invalid_geom_path.name}")

dissolved = dissolved[dissolved.geometry.type.isin(valid_types)]

# === Step 8: Save as Shapefile
print(f"💾 Saving output as Shapefile to {output_path}")
dissolved.to_file(output_path)

print("✅ Done! Shapefile created with centroid shift, area acres, and reassigned GEOIDs.")
