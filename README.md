# sjtdm-modern

This repository contains Python tools developed by the South Jersey Transportation Planning Organization (SJTPO) for modernizing the South Jersey Travel Demand Model (SJTDM). The focus is on aligning legacy Traffic Analysis Zones (TAZs) to 2020 U.S. Census Block Groups, performing QA/QC, and supporting long-term planning work.

> 📍 Project Directory: `J:\TAZ_Adustment\sjtdm-modern`

---

## 📁 Folder Structure

| Folder       | Description                                                              |
|--------------|--------------------------------------------------------------------------|
| `Docs/`      | Versioned documentation and technical notes                              |
| `inputs/`    | Lightweight input files needed by scripts (e.g., field mappings)         |
| `outputs/`   | Script-generated shapefiles, reports, and QA outputs (Git-ignored)       |
| `M365/`      | Microsoft Office-related utilities (batch converters, etc.)              |
| *(root)*     | Python scripts for TAZ adjustment, QA, and post-processing               |

---

## 🧰 Key Script Categories

| Script Pattern         | Description                                                       |
|------------------------|-------------------------------------------------------------------|
| `TAZ_AdjustV*.py`      | Main logic for realigning 2011 TAZs to 2020 CBGs                  |
| `TAZ_QA_V*.py`         | QA reporting scripts to check geometry accuracy and flag issues   |
| `adjust*.py`           | Older adjustment scripts (preserved for comparison/testing)       |
| `Merge_on_GEOIDv*.py`  | Utilities to merge adjusted shapefiles with Census attributes     |
| `Test_*.py`            | Standalone tests or experimental modules                          |

---

## 🧪 Environment

This project is developed in Python 3.12 using Conda.

To replicate the full environment (if `environment.yml` is provided):

```bash
conda env create -f environment.yml
conda activate RDRenv
