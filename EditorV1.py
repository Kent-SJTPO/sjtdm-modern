import arcpy
from arcpy import management as DM

def merge_selected_tazs(taz_fc, output_fc, orig_taz_fc):
    arcpy.env.overwriteOutput = True

    selected_layer = "selected_taz"
    arcpy.MakeFeatureLayer_management(taz_fc, selected_layer)
    arcpy.SelectLayerByAttribute_management(selected_layer, "NEW_SELECTION", "")
    selected_count = int(arcpy.GetCount_management(selected_layer)[0])

    if selected_count != 2:
        arcpy.AddError("Select exactly two polygons: source (to remove) and destination (to keep).")
        return

    selected = "in_memory\\selected"
    arcpy.CopyFeatures_management(selected_layer, selected)

    # Get selected features by OID
    with arcpy.da.SearchCursor(selected, ["OID@", "SHAPE@", "TAZ_112011"]) as cursor:
        features = sorted(list(cursor), key=lambda x: x[0])  # by OID
        source_oid, source_geom, source_taz = features[0]
        dest_oid, dest_geom, dest_taz = features[1]

    # Get original centroid of destination TAZ
    orig_centroid = None
    with arcpy.da.SearchCursor(orig_taz_fc, ["TAZ_112011", "SHAPE@"], where_clause=f"TAZ_112011 = '{dest_taz}'") as orig_cursor:
        for row in orig_cursor:
            orig_centroid = row[1].centroid
            break

    # Merge geometries
    merged_geom = dest_geom.union(source_geom)

    # Update destination geometry and recalc fields
    with arcpy.da.UpdateCursor(
        taz_fc,
        ["OID@", "SHAPE@", "area_acres", "centroid_x", "centroid_y", "centroid_d"]
    ) as cursor:
        for row in cursor:
            if row[0] == dest_oid:
                row[1] = merged_geom
                row[2] = merged_geom.area / 43560.0
                cen = merged_geom.centroid
                row[3] = cen.X
                row[4] = cen.Y
                if orig_centroid:
                    dx = cen.X - orig_centroid.X
                    dy = cen.Y - orig_centroid.Y
                    row[5] = (dx**2 + dy**2) ** 0.5
                else:
                    row[5] = None
                cursor.updateRow(row)

    # Delete source polygon
    DM.DeleteFeatures(taz_fc, f'"OBJECTID" = {source_oid}')

    # Save to output
    DM.CopyFeatures(taz_fc, output_fc)
    arcpy.AddMessage("✅ Merge complete.")

def main():
    taz_fc = arcpy.GetParameterAsText(0)
    output_fc = arcpy.GetParameterAsText(1)
    orig_taz_fc = arcpy.GetParameterAsText(2)
    merge_selected_tazs(taz_fc, output_fc, orig_taz_fc)

if __name__ == "__main__":
    main()
