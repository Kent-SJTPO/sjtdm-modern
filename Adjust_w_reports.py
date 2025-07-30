import geopandas as gpd
from pathlib import Path
from shapely.geometry import Point
import pandas as pd

# Define input and output paths
taz_path = Path(r"J:\TAZ_Adustment\Input\2010GIS\SJTDM Final TAZ_Nov2011.shp")
bg_path = Path(r"J:\TAZ_Adustment\Input\2020GIS\tl_2022_34_bg.shp")
output_path = Path(r"J:\TAZ_Adustment\Output\adjusted_taz_by_bg.shp")
csv_path = Path(r"J:\TAZ_Adustment\Output\taz_area_centroid_comparison.csv")

print("🔄 Loading TAZ shapefile...")
taz_gdf = gpd.read_file(taz_path)

print("🔄 Loading 2020 Census Block Groups...")
bg_gdf = gpd.read_file(bg_path)

# Filter only for SJTPO counties: Atlantic (001), Cape May (009), Cumberland (011), Salem (033)
print("📍 Filtering for Atlantic, Cape May, Cumberland, and Salem counties...")
target_counties = ["001", "009", "011", "033"]
bg_gdf = bg_gdf[bg_gdf["COUNTYFP"].isin(target_counties)]

print("🧭 Reprojecting to EPSG:3424 for accurate area and distance calculations...")
taz_gdf = taz_gdf.to_crs(epsg=3424)
bg_gdf = bg_gdf.to_crs(epsg=3424)

print("🔗 Performing spatial intersection...")
intersection = gpd.overlay(bg_gdf, taz_gdf[['TRACT2010', 'geometry']], how='intersection', keep_geom_type=False)
intersection['area'] = intersection.geometry.area

print("🧮 Assigning each BG to the dominant TAZ by area...")
intersection = intersection.sort_values('area', ascending=False)
dominant_taz = intersection.drop_duplicates(subset='GEOID')[['GEOID', 'TRACT2010']]

# Merge dominant TAZ back to the full filtered BG file
bg_gdf = bg_gdf.merge(dominant_taz, on='GEOID', how='left')

print(f"💾 Saving adjusted BG shapefile to {output_path}...")
bg_gdf.to_file(output_path)

# ======= BEGIN COMPARISON ANALYSIS =======
print("📏 Calculating original TAZ areas and centroids...")
taz_gdf['orig_area_sqft'] = taz_gdf.geometry.area
taz_gdf['orig_centroid'] = taz_gdf.geometry.centroid

print("🧩 Reconstructing new TAZ geometries from assigned Block Groups...")
new_taz = bg_gdf.dropna(subset=['TRACT2010']).dissolve(by='TRACT2010')
new_taz['new_area_sqft'] = new_taz.geometry.area
new_taz['new_centroid'] = new_taz.geometry.centroid

print("🔗 Merging original and new TAZ data for comparison...")
taz_compare = taz_gdf.set_index('TRACT2010')[['orig_area_sqft', 'orig_centroid']].join(
    new_taz[['new_area_sqft', 'new_centroid']], how='inner'
).dropna()

print("📐 Calculating centroid shift distances...")
taz_compare['centroid_shift_ft'] = taz_compare.apply(
    lambda row: row['orig_centroid'].distance(row['new_centroid']),
    axis=1
)

print("📊 Creating summary table with TAZ ID as first column...")
summary_df = taz_compare.reset_index()
summary_df = summary_df[['TRACT2010', 'orig_area_sqft', 'new_area_sqft', 'centroid_shift_ft']]
summary_df.rename(columns={
    'TRACT2010': 'TAZ_2010',
    'orig_area_sqft': 'Original_TAZ_Area_sqft',
    'new_area_sqft': 'New_TAZ_Area_sqft',
    'centroid_shift_ft': 'Centroid_Distance_ft'
}, inplace=True)

print(f"💾 Saving summary table to {csv_path}...")
summary_df.to_csv(csv_path, index=False)

print("✅ All processing complete.")
