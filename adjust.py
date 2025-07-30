import geopandas as gpd
import os

# === File paths ===
taz_path = r"J:\TAZ_Adustment\Input\2010GIS\SJTDM_Final_TAZ_Nov2011.shp"
bg_path = r"J:\TAZ_Adustment\Input\2020GIS\tl_2022_34_bg.shp"
output_path = r"J:\TAZ_Adustment\Output\adjusted_taz.shp"

# === Load shapefiles ===
print("🔄 Loading TAZ shapefile...")
taz_gdf = gpd.read_file(taz_path)

print("🔄 Loading full NJ Census Block Groups...")
bg_gdf = gpd.read_file(bg_path)

# === Filter Block Groups for SJTPO counties only ===
print("🔍 Filtering for Atlantic, Cape May, Cumberland, and Salem counties...")
sjtpo_counties = ["001", "009", "011", "033"]
bg_gdf = bg_gdf[bg_gdf["COUNTYFP"].isin(sjtpo_counties)]

# === Ensure both layers use the same CRS ===
if bg_gdf.crs != taz_gdf.crs:
    print("🔁 Reprojecting Block Groups to match TAZ CRS...")
    bg_gdf = bg_gdf.to_crs(taz_gdf.crs)

# === Perform spatial overlay ===
print("🔗 Performing spatial intersection...")
intersection = gpd.overlay(bg_gdf, taz_gdf[['TRACT2010', 'geometry']], how='intersection', keep_geom_type=True)

# === Calculate area for each intersected polygon ===
print("📐 Calculating area...")
intersection = intersection.to_crs(epsg=6539)  # Use NJ State Plane (ft) or EPSG:3857 if preferred
intersection["area_sqft"] = intersection.geometry.area

# === Export output shapefile ===
print("💾 Saving output shapefile...")
intersection = intersection.to_crs(taz_gdf.crs)  # Optional: revert back to original CRS
intersection.to_file(output_path)

print("✅ Done! Output saved to:", output_path)
