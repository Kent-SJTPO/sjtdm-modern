import geopandas as gpd
from pathlib import Path

# --- File paths ---
taz_path = Path(r"J:\TAZ_Adustment\Input\2010GIS\SJTDM Final TAZ_Nov2011.shp")
cbg_path = Path(r"J:\TAZ_Adustment\Input\2020GIS\tl_2022_34_bg.shp")
output_path = Path(r"J:\TAZ_Adustment\Output\2020TAZsV5.shp")

# --- Load shapefiles ---
print("🔄 Loading 2010 TAZs and 2020 CBGs...")
taz = gpd.read_file(taz_path)
cbg = gpd.read_file(cbg_path)

# --- Reproject if needed (to NJ State Plane US Feet) ---
if taz.crs.is_geographic:
    taz = taz.to_crs(epsg=6539)
if cbg.crs.is_geographic:
    cbg = cbg.to_crs(epsg=6539)

# --- Step 1: Intersect TAZs with 2020 Block Groups ---
print("📐 Intersecting TAZs (TAZ_112011) with 2020 CBGs...")
intersect = gpd.overlay(taz[['TAZ_112011', 'geometry']], cbg[['GEOID', 'geometry']], how='intersection')

# --- Step 2: Extract 2020 GEOID block group code and GEOID5 ---
intersect["GEOID2020"] = intersect["GEOID"].str[-7:]      # Last 7 digits (block group code)
intersect["GEOID5"] = intersect["GEOID2020"].str[:5]       # First 5 digits of that

# --- Step 3: Dissolve by TAZ_112011 + GEOID5 ---
print("🔁 Merging by TAZ_112011 + GEOID5...")
intersect["TAZ_GEOID5"] = intersect["TAZ_112011"].astype(str) + "_" + intersect["GEOID5"]
dissolved = intersect.dissolve(by="TAZ_GEOID5", as_index=False)

# --- Step 4: Clean fields ---
dissolved["TAZ_112011"] = dissolved["TAZ_112011"]
dissolved["GEOID5"] = dissolved["GEOID5"]
dissolved["GEOID2020"] = dissolved["GEOID2020"]
final = dissolved.drop(columns=["TAZ_GEOID5"])

# --- Save to shapefile ---
print(f"💾 Saving output to {output_path}")
final.to_file(output_path)

print("🎉 Done: TAZs split by 2020 CBGs and merged by TAZ_112011 + GEOID5.")
