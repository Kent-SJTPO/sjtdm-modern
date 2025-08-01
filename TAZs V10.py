import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from pathlib import Path

# --- SETTINGS ---
projected_crs = "EPSG:6539"  # NJ State Plane (US Feet)
taz_path = Path(r"J:\TAZ_Adustment\Input\2010GIS\SJTDM Final TAZ_Nov2011.shp")
cbg_path = Path(r"J:\TAZ_Adustment\Input\2020GIS\tl_2022_34_bg.shp")
output_path = Path(r"J:\TAZ_Adustment\Output\adjusted_taz_cbgaligned.shp")
sliver_threshold_acres = 2

# --- LOAD DATA ---
print("🔄 Loading and projecting shapefiles...")
taz = gpd.read_file(taz_path).to_crs(projected_crs)
cbg = gpd.read_file(cbg_path).to_crs(projected_crs)

# --- PREPROCESS ---
taz["TAZ_112011"] = taz["TAZ_112011"].astype(str)
cbg["GEOID5"] = cbg["GEOID"].str[-5:]

# Store original centroid and area
taz["Orig_CenX"] = taz.geometry.centroid.x
taz["Orig_CenY"] = taz.geometry.centroid.y
taz["Orig_Acres"] = taz.geometry.area / 43560

# --- STEP 1: Preserve TAZs fully within one CBG ---
print("✅ Finding TAZs fully contained within single CBG...")
preserved = gpd.overlay(taz, cbg, how='intersection', keep_geom_type=True)
preserved["overlap_area"] = preserved.geometry.area
overlap_summary = preserved.groupby("TAZ_112011")["GEOID5"].nunique().reset_index()
single_cbgs = overlap_summary[overlap_summary["GEOID5"] == 1]["TAZ_112011"]
preserved_taz = taz[taz["TAZ_112011"].isin(single_cbgs)].copy()
preserved_taz = gpd.sjoin(preserved_taz, cbg[["GEOID5", "geometry"]], how="left", predicate="within")
preserved_taz["geometry_f"] = "preserved"

# --- STEP 2: Intersect and split remaining TAZs by CBG ---
print("📐 Intersecting remaining TAZs...")
remaining_taz = taz[~taz["TAZ_112011"].isin(single_cbgs)]
intersected = gpd.overlay(remaining_taz, cbg[["GEOID5", "geometry"]], how="intersection", keep_geom_type=True)
intersected["geometry_f"] = "split"
intersected["area_acres"] = intersected.geometry.area / 43560

# --- STEP 3: Handle slivers < threshold ---
print("🧹 Reassigning small polygons...")
def reassign_slivers(gdf, threshold):
    slivers = gdf[gdf["area_acres"] < threshold].copy()
    keepers = gdf[gdf["area_acres"] >= threshold].copy()
    reassigned = []

    for idx, sliver in slivers.iterrows():
        neighbors = keepers[keepers["GEOID5"] == sliver["GEOID5"]].copy()
        neighbors["shared_len"] = neighbors.geometry.boundary.intersection(sliver.geometry.boundary).length
        if not neighbors.empty and neighbors["shared_len"].max() > 0:
            target_idx = neighbors["shared_len"].idxmax()
            keepers.loc[target_idx, "geometry"] = keepers.loc[target_idx, "geometry"].union(sliver.geometry)
        else:
            # Fallback: merge to nearest
            keepers["dist"] = keepers.geometry.centroid.distance(sliver.geometry.centroid)
            target_idx = keepers["dist"].idxmin()
            keepers.loc[target_idx, "geometry"] = keepers.loc[target_idx, "geometry"].union(sliver.geometry)
        reassigned.append(sliver["TAZ_112011"])

    return keepers

merged_polygons = reassign_slivers(intersected, sliver_threshold_acres)

# --- STEP 4: Combine and compute metadata ---
print("📊 Finalizing attributes...")
final = pd.concat([preserved_taz, merged_polygons], ignore_index=True)
final["area_acres"] = final.geometry.area / 43560
final["centroid_x"] = final.geometry.centroid.x
final["centroid_y"] = final.geometry.centroid.y

# --- STEP 5: Merge original TAZ attributes (centroids and area) ---
print("🔁 Merging original TAZ attributes...")
final = final.merge(
    taz[["TAZ_112011", "Orig_CenX", "Orig_CenY", "Orig_Acres"]],
    on="TAZ_112011", how="left"
)

# --- STEP 6: Calculate distance to original centroid ---
print("📏 Calculating centroid shift distance...")
orig_centroids = taz.set_index("TAZ_112011").geometry.centroid
centroid_dists = []

for idx, row in final.iterrows():
    taz_id = row["TAZ_112011"]
    orig_cen = orig_centroids.get(taz_id, None)
    new_cen = row.geometry.centroid
    if orig_cen is not None:
        centroid_dists.append(new_cen.distance(orig_cen))
    else:
        centroid_dists.append(None)

final["centroid_d"] = centroid_dists

# --- STEP 7: Save output ---
print(f"💾 Saving output to {output_path}...")
final.to_file(output_path)

print("✅ Conversion complete.")
