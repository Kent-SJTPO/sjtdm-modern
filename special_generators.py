import pandas as pd
import os

print("Special Generator Trip File Builder Starting...")

# === Step 1: Define special generators manually ===
# Later, you can pull this from land use, counts, or seasonal logic
data = {
    "TAZ_ID": [9123, 9250, 9134],
    "GEN_TYPE": ["Airport", "College", "Mall"],
    "DAILY_TRIPS": [5000, 8500, 3200],
    "COMMENT": [
        "AC International Airport",
        "Stockton University (Main Campus)",
        "Hamilton Mall (retail complex)"
    ]
}

df = pd.DataFrame(data)

# === Step 2: Save to output folder ===
output_folder = "outputs"
os.makedirs(output_folder, exist_ok=True)

output_path = os.path.join(output_folder, "special_generators.csv")
df.to_csv(output_path, index=False)

print(f"✅ Special generator file created at {output_path}")
