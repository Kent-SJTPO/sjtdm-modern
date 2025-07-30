import geopandas as gpd
from pathlib import Path

# File paths
taz_path = Path(r"J:\TAZ_Adustment\Input\2010GIS\SJTDM Final TAZ_Nov2011.shp")
tract_path = Path(r"J:\TAZ_Adustment\Input\2020GIS\tl_2022_34_bg.shp")
output_path = Path(r"J:\TAZ_Adustment\Output\adjusted_taz_preserved.shp")

# Load shapefiles
print("🔄 Loading shapefiles...")
taz_gdf = gpd.read_file(taz_path)
tract_gdf = gpd.read_file(tract_path)

# Project both to NJ State Plane (ft)
projected_crs = "EPSG:3424"
taz_gdf = taz_gdf.to_crs(projected_crs)
tract_gdf = tract_gdf.to_crs(projected_crs)

# Output container
adjusted_list = []

print("⚙️ Processing TAZs...")
for _, taz_row in taz_gdf.iterrows():
    taz_geom = taz_row.geometry
    taz_id = taz_row["TAZ_112011"]

    overlapping_tracts = tract_gdf[tract_gdf.intersects(taz_geom)]

    if len(overlapping_tracts) == 1:
        # ✅ Fully within one tract — preserve as-is
        tract_code = overlapping_tracts.iloc[0]["GEOID"]
        adjusted_list.append({
            "TAZID": taz_id,
            "TRACT2010": tract_code,
            "Preserved": 1,
            "geometry": taz_geom
        })
    else:
        # ❗ Split TAZ using overlay, keep only polygon geometries
        taz_single = gpd.GeoDataFrame([taz_row], crs=projected_crs)
        intersected = gpd.overlay(overlapping_tracts, taz_single, how="intersection", keep_geom_type=True)
        for _, part in intersected.iterrows():
            tract_code = part["GEOID"]
            adjusted_list.append({
                "TAZID": taz_id,
                "TRACT2010": tract_code,
                "Preserved": 0,
                "geometry": part.geometry
            })

# Convert to GeoDataFrame
adjusted_gdf = gpd.GeoDataFrame(adjusted_list, crs=projected_crs)

# Save to shapefile
print(f"💾 Saving output to {output_path}...")
adjusted_gdf.to_file(output_path)

print("✅ Done. Adjusted TAZs written with TAZ112011 as ID.")
