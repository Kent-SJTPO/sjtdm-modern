import geopandas as gpd
import pandas as pd
from pathlib import Path

# === File paths ===
taz_2020_path = Path(r"J:\TAZ_Adustment\Output\2020TAZsV11.shp")
taz_2011_path = Path(r"J:\TAZ_Adustment\Input\2010GIS\SJTDM FINAL TAZ_NOV2011.shp")
output_path = Path(r"J:\TAZ_Adustment\Output\2020TAZsQA.shp")

# === Load shapefiles ===
print("🔄 Loading TAZ shapefiles...")
taz20 = gpd.read_file(taz_2020_path)
taz11 = gpd.read_file(taz_2011_path)

# === Project both to NJ State Plane (EPSG:6539, US Feet) ===
taz20 = taz20.to_crs(epsg=6539)
taz11 = taz11.to_crs(epsg=6539)

# === Ensure ID is string for reliable join ===
taz20['TAZ_112011'] = taz20['TAZ_112011'].astype(str)
taz11['TAZ_112011'] = taz11['TAZ_112011'].astype(str)

# === Compute areas in ACRES and centroids ===
print("📐 Calculating area (acres) and centroids...")
taz20['Area20'] = (taz20.geometry.area / 43560).round(2)
taz20['Cent20'] = taz20.geometry.centroid

taz11['Area11'] = (taz11.geometry.area / 43560).round(2)
taz11['Cent11'] = taz11.geometry.centroid

# === Prepare 2011 attributes with _11 suffix ===
taz11_attrs = taz11.drop(columns='geometry').copy()
taz11_attrs = taz11_attrs.rename(columns={
    col: f"{col}_11" for col in taz11_attrs.columns
    if col not in ['TAZ_112011', 'Area11', 'Cent11']
})

# === Merge TAZs on TAZ_112011 ===
print("🔗 Merging datasets...")
merged = taz20.merge(taz11_attrs, on='TAZ_112011', how='outer', indicator=True)

# === QA Flag Function ===
def flag_record(row):
    flags = []
    diffpct = None
    centdist = None

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
            diffpct = round(abs((area_20 - area_11) / area_11 * 100), 2)
            if diffpct > 5:
                flags.append("AreaMismatch")

        if pd.notnull(cent_20) and pd.notnull(cent_11):
            try:
                centdist = round(cent_11.distance(cent_20), 1)
                if centdist > 500:
                    flags.append("CentroidMismatch")
            except:
                centdist = None

    flag = "|".join(flags) if flags else "OK"
    return pd.Series([flag, diffpct, centdist])

# === Apply flag logic and assign new fields ===
print("🚩 Applying QA checks...")
merged[['Flag', 'DiffPct', 'CentDist']] = merged.apply(flag_record, axis=1)

# === Clean up before saving ===
print("🧼 Cleaning up output fields...")
columns_to_drop = ['Cent20', 'Cent11', '_merge', 'Shape_Area', 'Shape_Leng']
merged.drop(columns=columns_to_drop, inplace=True, errors='ignore')

# === Save output shapefile ===
print("💾 Writing cleaned QA shapefile...")
merged = merged.set_geometry('geometry')
merged.to_file(output_path)

print(f"✅ QA complete. Output saved to:\n{output_path}")
