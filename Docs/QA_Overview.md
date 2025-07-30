# TAZ QA Output Overview

This document explains the key fields produced by the `TAZ_QA_V*.py` scripts used in the `sjtdm-modern` project. These scripts generate a QA shapefile to evaluate the spatial accuracy and integrity of the realigned Traffic Analysis Zones (TAZs).

---

## 📐 Purpose

The QA shapefile allows reviewers to:
- Validate how closely adjusted TAZs match their original boundaries
- Detect excessive centroid shifts or area mismatches
- Identify potential geometry issues using standardized flags

---

## 📊 Key Fields in the QA Output

| Field Name   | Description                                                                 |
|--------------|-----------------------------------------------------------------------------|
| `TAZ_112011` | Original 2011 TAZ identifier                                                |
| `TAZ_NEW`    | New TAZ identifier from the adjusted geometry                               |
| `GEOID5`     | 5-digit Census Block Group (CBG) GEOID associated with the adjusted zone    |
| `AreaAcres`  | Area of the adjusted TAZ in acres                                           |
| `AreaDiff`   | Area difference in acres between original and adjusted TAZ                 |
| `Diffpct`    | **Percent area change** from original to adjusted geometry:<br>`(AreaDiff / OriginalArea) * 100` |
| `CentDist`   | **Distance in feet** between the original and adjusted TAZ centroids       |
| `CentX`, `CentY` | X/Y coordinates of adjusted centroid                                     |
| `Flag`       | Geometry or logic-based QA flag:<br>`0 = OK`, `1 = Review required`        |
| `Notes`      | Optional descriptive note for internal review                              |

---

## 🚩 Flag Logic

The `Flag` field is determined by a combination of automated QA checks, typically based on thresholds such as:

- **Area Difference** exceeds ±15% → `Flag = 1`
- **Centroid Shift** exceeds 0.25 miles (1320 ft) → `Flag = 1`
- **Invalid or null geometry** → `Flag = 1`

> Flags are cumulative — if any QA check fails, the record is marked for review.

---

## 📎 Usage Notes

- This QA file is written to the `outputs/` folder as a shapefile (e.g., `2020TAZsQA.shp`)
- Outputs can be reviewed in ArcGIS Pro or QGIS using symbology and attribute filters
- Scripts using these fields include:
  - `TAZ_QA_V3.py`
  - `TAZ_QA_V4.py`

---

## 🔧 Customization

Thresholds and output field names can be modified in the script header of each QA script (`TAZ_QA_V*.py`).

Please document any edits to the logic in the `Docs/Version_Change_Log.md`.

