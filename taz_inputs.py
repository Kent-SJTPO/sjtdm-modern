import pandas as pd
import os

print("TAZ Socioeconomic Input Builder Starting...")

# === Step 1: Create Sample Data ===
# (Replace these rows with actual projections when ready)
data = {
    "TAZ_ID": [101, 102, 103, 104],
    "HOUSEHOLDS": [1250, 980, 675, 1500],
    "EMPLOYMENT": [600, 1200, 300, 750],
    "STUDENTS": [150, 100, 80, 200],
    "AREA_TYPE": [2, 1, 3, 2]
}

df = pd.DataFrame(data)

# === Step 2: Save to Outputs Folder ===
output_folder = "outputs"
os.makedirs(output_folder, exist_ok=True)

output_path = os.path.join(output_folder, "taz_inputs.csv")
df.to_csv(output_path, index=False)

print(f"✅ TAZ input file created at {output_path}")
