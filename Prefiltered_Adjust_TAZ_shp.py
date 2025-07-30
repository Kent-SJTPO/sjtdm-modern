import geopandas as gpd
from pathlib import Path

# Define input and output paths
taz_path = Path(r"J:\TAZ_Adustment\Input\2010GIS\SJTDM Final TAZ_Nov2011.shp")
bg_path = Path(r"J:\TAZ_Adustment\Input\2020GIS\tl_2022_34_bg.shp")
output_path = Path(r"J:\TAZ_Adustment\Output\adjusted_taz_by_bg.shp")

print("🔄 Loading TAZ shapefile...")
taz_gdf = gpd.read_file(taz_path)

print("🔄 Loading 2020 Census Block Groups...")
bg_gdf = gpd.read_file(bg_path)

# Filter only for SJTPO counties: Atlantic (001), Cape May (009), Cumberland (011), Salem (033)
print("📍 Filtering for Atlantic, Cape May, Cumberland, and Salem counties...")
target_counties = ["001", "009", "011", "033"]
bg_gdf = bg_gdf[bg_gdf["COUNTYFP"].isin(target_counties)]

print("🧭 Reprojecting to EPSG:3424 for accurate area calculations...")
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

print(f"💾 Saving output to {output_path}...")
bg_gdf.to_file(output_path)

print("✅ Shapefile export complete.")
