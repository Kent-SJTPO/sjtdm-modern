import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from pathlib import Path

# === File paths ===
taz_2020_path = Path(r"J:\TAZ_Adustment\Output\2020TAZsV11.shp")
taz_2011_path = Path(r"J:\TAZ_Adustment\Input\2010GIS\SJTDM FINAL TAZ_NOV2011.shp")
output_path = Path(r"J:\TAZ_Adustment\Output\2020TAZsQA.shp")

# === Load shapefiles ===
print("🔄 Loading TAZ shapefiles...")
taz20 = gpd.read_file(taz_2020_path)
taz11 = gpd.read_file(taz_2011_path)

# === Project to NJ State Plane (feet) ===
taz20 = taz20.to_crs(epsg=6539)
taz11 = taz11.to_crs(epsg=6539)

# === Ensure ID field is string ===
taz20['TAZ_112011'] = taz20['TAZ_112011'].astype(str)
taz11['TAZ_112011'] = taz11['TAZ_112011'].astype(str)

# === Compute areas in ACRES and centroids ===
print("📐 Calculating area (acres) and centroids...")
taz20['Area20'] = taz20.geometry.area / 43560
taz20['Cent20'] = taz20.geometry.centroid

taz11['Area11'] = taz11.geometry.area / 43560
taz11['Cent11'] = taz11.geometry.centroid

# === Prepare original attributes with suffix ===
taz11_attrs = taz11.drop(columns='geometry').copy()
taz11_attrs = taz11_attrs.rename(columns={
    col: f"{col}_11" for col in taz11_attrs.columns
    if col not in ['TAZ_112011', 'Area11', 'Cent11']
})

# === Merge on TAZ_112011 ===
print("🔗 Merging 2011 and 2020 TAZs...")
merged = taz20.merge(taz11_attrs, on='TAZ_112011', how='outer', indicator=True)

# === Initialize QA columns ===
merged['DiffPct'] = None
merged['CentDist'] = None

# === Flag function ===
def flag_record(row):
    flags = []

    if row['_merge'] == 'left_only':
        flags.append("Missing_in_2011")
    elif row['_merge'] == 'right_only':
        flags.append("Missing_in_2020")
    else:
        area_20 = row.get('Area20')
        area_11 = row.get('Area11')
        cent_20 = row.get('Cent20')
        cent_11 = row.get('Cent11')

        if pd.notnull(area_20) and pd.notnull(area_11) and area_11 > 0:
            pct_diff = abs((area_20 - area_11) / area_11 * 100)
            row['DiffPct'] = pct_diff
            if pct_diff > 5:
                flags.append("AreaMismatch")

        if pd.notnull(cent_20) and pd.notnull(cent_11):
            try:
                dist = cent_11.distance(cent_20)
                row['CentDist'] = dist
                if dist > 500:
                    flags.append("CentroidMismatch")
            except:
                row['CentDist'] = None

    return "|".join(flags) if flags else "OK"

# === Apply QA flags ===
print("🚩 Flagging discrepancies...")
merged['Flag'] = merged.apply(flag_record, axis=1)

# === Round numeric fields for shapefile limits ===
merged['Area11'] = merged['Area11'].round(2)
merged['Area20'] = merged['Area20'].round(2)
merged['DiffPct'] = merged['DiffPct'].round(2)
merged['CentDist'] = merged['CentDist'].round(1)

# === Finalize geometry and clean up ===
print("💾 Writing to shapefile...")
merged = merged.set_geometry('geometry')
merged.drop(columns=['Cent20', 'Cent11', '_merge'], inplace=True, errors='ignore')
merged.to_file(output_path)

print(f"✅ QA complete. Output saved to:\n{output_path}")
