import geopandas as gpd
from pathlib import Path

# File paths
taz_path = Path(r"J:\TAZ_Adustment\Input\2010GIS\SJTDM Final TAZ_Nov2011.shp")
bg_path = Path(r"J:\TAZ_Adustment\Input\2020GIS\tl_2022_34_bg.shp")
output_shp = Path(r"J:\TAZ_Adustment\Output\adjusted_taz_preserved_enhanced.shp")
summary_csv = Path(r"J:\TAZ_Adustment\Output\taz_adjustment_summary.csv")

# Load and reproject
print("🔄 Loading and projecting data...")
taz_gdf = gpd.read_file(taz_path).to_crs("EPSG:3424")
bg_gdf = gpd.read_file(bg_path).to_crs("EPSG:3424")

# Prepare original TAZ metrics
taz_gdf["source_area"] = taz_gdf.geometry.area
taz_gdf["source_centroid"] = taz_gdf.geometry.centroid

# Start processing
adjusted = []
print("⚙️ Processing TAZs...")
for _, taz in taz_gdf.iterrows():
    taz_id = taz["TAZ_112011"]
    taz_geom = taz.geometry
    source_area = taz["source_area"]
    source_centroid = taz["source_centroid"]

    overlaps = bg_gdf[bg_gdf.intersects(taz_geom)]

    if len(overlaps) == 1:
        bg_row = overlaps.iloc[0]
        tract = bg_row["TRACTCE"]
        geoid2020 = bg_row["GEOID"][-6:]  # Keep only tract + block group
        dest_geom = taz_geom
        dest_centroid = dest_geom.centroid
        adjusted.append({
            "TAZID": taz_id,
            "TRACT2010": tract,
            "GEOID2020": geoid2020,
            "Preserved": 1,
            "area_sft": dest_geom.area,
            "source_area": source_area,
            "centroid_shift": source_centroid.distance(dest_centroid),
            "geometry": dest_geom
        })
    else:
        taz_one = gpd.GeoDataFrame([taz], crs=taz_gdf.crs)
        split = gpd.overlay(overlaps, taz_one, how="intersection", keep_geom_type=True)
        for _, part in split.iterrows():
            tract = part["TRACTCE"]
            geoid2020 = part["GEOID"][-6:]  # Keep only tract + block group
            dest_geom = part.geometry
            dest_centroid = dest_geom.centroid
            adjusted.append({
                "TAZID": taz_id,
                "TRACT2010": tract,
                "GEOID2020": geoid2020,
                "Preserved": 0,
                "area_sft": dest_geom.area,
                "source_area": source_area,
                "centroid_shift": source_centroid.distance(dest_centroid),
                "geometry": dest_geom
            })

# Build GeoDataFrame
adjusted_gdf = gpd.GeoDataFrame(adjusted, crs=taz_gdf.crs)

# Convert area to acres and round values
adjusted_gdf["area_acres"] = (adjusted_gdf["area_sft"] / 43560).round(2)
adjusted_gdf["source_acres"] = (adjusted_gdf["source_area"] / 43560).round(2)
adjusted_gdf["centroid_shift"] = adjusted_gdf["centroid_shift"].round(2)

# Drop square feet columns
adjusted_gdf = adjusted_gdf.drop(columns=["area_sft", "source_area"])

# Save outputs
print(f"💾 Saving shapefile to {output_shp}...")
adjusted_gdf.to_file(output_shp)

print(f"📄 Saving summary to {summary_csv}...")
adjusted_gdf.drop(columns="geometry").to_csv(summary_csv, index=False)

print("✅ Enhanced TAZ adjustment complete.")



