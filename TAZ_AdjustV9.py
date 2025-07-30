import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path

# === File Paths ===
taz_path = Path(r"J:\TAZ_Adustment\Input\2010GIS\SJTDM Final TAZ_Nov2011.shp")
cbg_path = Path(r"J:\TAZ_Adustment\Input\2020GIS\tl_2022_34_bg.shp")
output_path = Path(r"J:\TAZ_Adustment\Output\2020TAZsV9_with_centroids.shp")
audit_log_path = Path(r"J:\TAZ_Adustment\Output\reassigned_small_parcels_v9.csv")
invalid_geom_path = Path(r"J:\TAZ_Adustment\Output\TAZv9_invalid_geometry.gpkg")

# === Load Files ===
print("🔄 Loading TAZ and CBG files...")
taz = gpd.read_file(taz_path)
cbg = gpd.read_file(cbg_path)

# === Project to NJ State Plane (ft) ===
if taz.crs.is_geographic:
    taz = taz.to_crs(epsg=6539)
if cbg.crs.is_geographic:
    cbg = cbg.to_crs(epsg=6539)

# === Step 0: Identify Pass-through TAZs that don't meaningfully cross CBGs ===
print("🔍 Preprocessing: Identifying TAZs that do not meaningfully cross 2020 boundaries...")
taz["TAZ_ID"] = taz["TAZ_112011"]
taz["TAZ_area_ft2"] = taz.geometry.area
taz["TAZ_area_acres"] = taz["TAZ_area_ft2"] / 43560

# Overlay for intersection
taz_cbg_join = gpd.overlay(taz[['TAZ_ID', 'geometry']], cbg[['GEOID', 'geometry']], how="intersection", keep_geom_type=False)
taz_cbg_join["int_area_ft2"] = taz_cbg_join.geometry.area

# Identify primary CBG for each TAZ
top_cbg = taz_cbg_join.sort_values("int_area_ft2", ascending=False).drop_duplicates("TAZ_ID")
taz_cbg_join = taz_cbg_join.merge(top_cbg[['TAZ_ID', 'GEOID', 'int_area_ft2']], on="TAZ_ID", suffixes=("", "_max"))
taz_cbg_join["pct_primary"] = taz_cbg_join["int_area_ft2_max"] / taz_cbg_join.groupby("TAZ_ID")["int_area_ft2"].transform("sum")

# Count how many different CBGs intersect each TAZ
cbg_count = taz_cbg_join.groupby("TAZ_ID")["GEOID"].nunique().reset_index(name="cbg_count")

# Define pass-through criteria
pass_through_ids = cbg_count[
    (cbg_count["cbg_count"] == 1) |
    (taz_cbg_join.groupby("TAZ_ID")["pct_primary"].max().reset_index()["pct_primary"] > 0.95)
]["TAZ_ID"].tolist()

# Separate TAZs
taz_single = taz[taz["TAZ_ID"].isin(pass_through_ids)].copy()
taz_multi = taz[~taz["TAZ_ID"].isin(pass_through_ids)].copy()

# === Step 1: Intersect multi-CBG TAZs with 2020 Block Groups ===
print("📐 Performing spatial intersection...")
intersect = gpd.overlay(
    taz_multi[['TAZ_112011', 'geometry']],
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
print("🔍 Reassigning small parcels by closest GEOID...")
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

small = intersect["area_acres"] < SMALL_PARCEL_ACRES
intersect.loc[small, "GEOID2020_int"] = intersect.loc[small, "GEOID2020_int"].apply(
    lambda x: find_closest_geoid(x, valid_array, threshold=999)
)

# Post-check
unmatched = intersect.loc[small]
still_unmatched = ~unmatched["GEOID2020_int"].isin(valid_geoids)
print(f"⚠️ {still_unmatched.sum()} small parcels still unmatched after ±999 threshold")

# Audit log
intersect.loc[small, ["TAZ_112011", "GEOID", "GEOID2020_int", "area_acres"]].to_csv(
    audit_log_path, index=False
)

# Final GEOID
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
taz["TAZ_centroid"] = taz.geometry.centroid

dissolved = dissolved.merge(
    taz[['TAZ_112011', 'TAZ_area_acres', 'TAZ_centroid']],
    on='TAZ_112011', how='left'
)

dissolved["poly_area_acres"] = dissolved.geometry.area / 43560
dissolved["new_centroid"] = dissolved.geometry.centroid
dissolved["centroid_dist_ft"] = dissolved.apply(
    lambda row: row["new_centroid"].distance(row["TAZ_centroid"]), axis=1
)

dissolved = dissolved.drop(columns=["TAZ_centroid", "new_centroid", "TAZ_GEOID5", "final_GEOID2020"])

# === Step 7: Merge with taz_single ===
taz_single["GEOID2020"] = None
taz_single["GEOID5"] = None
taz_single["poly_area_acres"] = taz_single.geometry.area / 43560
taz_single["centroid_dist_ft"] = 0
taz_single["area_acres"] = taz_single["TAZ_area_acres"]

shared_cols = dissolved.columns.intersection(taz_single.columns)
final_output = pd.concat([dissolved[shared_cols], taz_single[shared_cols]], ignore_index=True)

# === Step 8: Filter invalid geometries ===
print("🧼 Filtering unsupported geometries for Shapefile output...")
valid_types = ["Polygon", "MultiPolygon"]
invalid = final_output[~final_output.geometry.type.isin(valid_types)]
if not invalid.empty:
    invalid.to_file(invalid_geom_path, driver="GPKG")
    print(f"⚠️ {len(invalid)} invalid geometries saved to {invalid_geom_path.name}")
final_output = final_output[final_output.geometry.type.isin(valid_types)]

# === Step 9: Save final shapefile ===
print(f"💾 Saving final output to {output_path}")
final_output.to_file(output_path)

print("✅ Done! V9 Shapefile created with tolerance-aware zone preservation.")
