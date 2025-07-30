import geopandas as gpd
from pathlib import Path

taz_path = Path(r"J:\TAZ_Adustment\Input\2010GIS\SJTDM Final TAZ_Nov2011.shp")
taz_gdf = gpd.read_file(taz_path)

print("🧾 Columns in TAZ shapefile:")
print(taz_gdf.columns)






