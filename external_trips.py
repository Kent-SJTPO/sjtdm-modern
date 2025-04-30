add-special-generators
import pandas as pd
import os

print("External Trip Builder Starting...")

# === Step 1: Define External Trip Data ===
# (You can replace these values with your real regional external forecasts later!)
external_data = {
    "EXTERNAL_ID": [9001, 9002, 9003, 9004],
    "P_TRIPS": [2500, 1800, 3200, 1500],
    "A_TRIPS": [2600, 1750, 3100, 1600],
}

df = pd.DataFrame(external_data)

# === Step 2: Create Outputs Folder if Needed ===
outputs_folder = "outputs"
os.makedirs(outputs_folder, exist_ok=True)

# === Step 3: Save External Trip File ===
output_path = os.path.join(outputs_folder, "external_trips.csv")
df.to_csv(output_path, index=False)

print(f"✅ External trips file created at {output_path}")
=======
import pandas as pd
import os

print("External Trip Builder Starting...")

# === Step 1: Define External Trip Data ===
# (You can replace these values with your real regional external forecasts later!)
external_data = {
    "EXTERNAL_ID": [9001, 9002, 9003, 9004],
    "P_TRIPS": [2500, 1800, 3200, 1500],
    "A_TRIPS": [2600, 1750, 3100, 1600],
}

df = pd.DataFrame(external_data)

# === Step 2: Create Outputs Folder if Needed ===
outputs_folder = "outputs"
os.makedirs(outputs_folder, exist_ok=True)

# === Step 3: Save External Trip File ===
output_path = os.path.join(outputs_folder, "external_trips.csv")
df.to_csv(output_path, index=False)

print(f"✅ External trips file created at {output_path}")
main
