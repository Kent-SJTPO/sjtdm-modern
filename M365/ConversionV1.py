import geopandas as gpd

# Define the EPSG codes
epsg_nad83 = 4269  # GCS_North_American_1983
epsg_njsp = 3424   # New Jersey State Plane feet

# Step 1: Read the shapefiles
taz_gdf = gpd.read_file("J:/TAZ_Adustment/Input/2010GIS/SJTDM Final TAZ_Nov2011.shp")
cbg_gdf = gpd.read_file("J:/TAZ_Adustment/Input/2020GIS/2020_CBG_SJTDM.shp")

# Step 2: Reproject to New Jersey State Plane feet
taz_gdf = taz_gdf.to_crs(epsg=epsg_njsp)
cbg_gdf = cbg_gdf.to_crs(epsg=epsg_njsp)

# Step 3: Perform a spatial join
# Use 'predicate' instead of 'op'
joined_gdf = gpd.sjoin(taz_gdf, cbg_gdf, how="inner", predicate="intersects")

# Step 4: Adjust the geometries
# This step depends on the specific rules you want to follow for the adjustment
# For simplicity, let's assume we just want to keep the intersection geometries
adjusted_gdf = joined_gdf.copy()
adjusted_gdf['geometry'] = adjusted_gdf.geometry.intersection(cbg_gdf.unary_union)

# Step 5: Calculate the new area in acres
# Note: Since the data is now in feet, we need to convert square feet to acres
adjusted_gdf['area_acres'] = adjusted_gdf.geometry.area / 43560  # Convert square feet to acres
# Step 6: Save the new shapefile
adjusted_gdf.to_file("J:/TAZ_Adustment/Output/First Run/adjusted_taz_2020v1.shp")

print("New shapefile created successfully!")r

