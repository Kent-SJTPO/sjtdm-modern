import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from pathlib import Path

# === File paths ===
taz_2020_path = Path(r"J:\TAZ_Adustment\Output\2020TAZsV11.shp")
taz_2011_path = Path(r"J:\TAZ_Adustment\Input\2010GIS\SJTDM FINAL TAZ_NOV2011.shp")
output_path = Path(r"J:\TAZ_Adustment\Output\2020TAZsQA.shp")

# === Load data ===
print("🔄 Loading shapefiles...")
taz20 = gpd.read_file(taz_2020_path)
taz11 = gpd.read_file(taz_2011_path)

# === Use projected CRS for NJ (feet) ===
taz20 = taz20.to_crs(epsg=6539)
taz11 = taz11.to_crs(epsg=6539)

# === Rename TAZ_112011 for clarity (if needed) ===
taz20['TAZ_112011'] = taz20['TAZ_112011'].astype(str)
taz11['TAZ_112011'] = taz11['TAZ_112011'].astype(str)

# === Calculate areas and centroids ===
print("📐 Calculating area and centroid...")
taz20['Area20'] = taz20.geometry.area
taz20['Cent20'] = taz20.geometry.centroid

taz11['Area11'] = taz11.geometry.area
taz11['Cent11'] = taz11.geometry.centroid

# === Calculate area and centroid BEFORE dropping geometry ===
taz11['Area11'] = taz11.geometry.area
taz11['Cent11'] = taz11.geometry.centroid

# === Prepare original TAZs with suffixes, but KEEP Area11 and Cent11 ===
taz11_attrs = taz11.drop(columns='geometry').copy()

# Suffix only non-key, non-QA columns
taz11_attrs = taz11_attrs.rename(columns={
    col: f"{col}_11" for col in taz11_attrs.columns
    if col not in ['TAZ_112011', 'Area11', 'Cent11']
})


# === Merge 2020 with 2011 attributes and centroids ===
print("🔗 Joining on TAZ_112011...")
merged = taz20.merge(taz11_attrs, on='TAZ_112011', how='outer', indicator=True)

# === Flag missing entries ===
print("🚩 Flagging missing and mismatched records...")
def flag_record(row):
    flags = []

    if row['_merge'] == 'left_only':
        flags.append("Missing_in_2011")
    elif row['_merge'] == 'right_only':
        flags.append("Missing_in_2020")
    else:
        # Matched record — check geometry
        area_20 = row['Area20']
        area_11 = row['Area11']
        cent_20 = row['Cent20']
        cent_11 = row['Cent11']

        if area_11 and area_20:
            pct_diff = abs((area_20 - area_11) / area_11 * 100)
            row['DiffPct'] = pct_diff
            if pct_diff > 5:
                flags.append("AreaMismatch")
        else:
            row['DiffPct'] = None

        if cent_11 and cent_20:
            dist = cent_11.distance(cent_20)
            row['CentDist'] = dist
            if dist > 500:
                flags.append("CentroidMismatch")
        else:
            row['CentDist'] = None

    return "|".join(flags) if flags else "OK"

merged['DiffPct'] = None
merged['CentDist'] = None
merged['Flag'] = merged.apply(flag_record, axis=1)

# === Keep only 2020 geometries ===
print("🗂 Preparing output shapefile...")
merged = merged.set_geometry('geometry')  # keep 2020 shapes

# Remove columns not allowed in shapefiles (e.g., geometry objects like Point)
merged.drop(columns=['Cent20', 'Cent11', '_merge'], inplace=True, errors='ignore')

# Save to shapefile
print("💾 Saving to shapefile...")
merged.to_file(output_path)

print(f"✅ QA complete. Output saved to:\n{output_path}")
