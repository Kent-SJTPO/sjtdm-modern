print("QA Script Starting...")
import pandas as pd
import os

# === Step 1: Read Generated Panda File ===
input_path = "outputs/panda.csv"
df = pd.read_csv(input_path)

# === Step 2: Create QA Output Folder ===
qa_folder = "outputs/qa"
os.makedirs(qa_folder, exist_ok=True)

# === Step 3: Check for Missing Values ===
missing_values = df[df.isnull().any(axis=1)]
if not missing_values.empty:
    missing_values.to_csv(f"{qa_folder}/missing_values.csv", index=False)
    print(f"⚠️  Found {len(missing_values)} rows with missing values.")
else:
    print("✅ No missing values found.")

# === Step 4: Check for Negative Values ===
numeric_cols = df.select_dtypes(include=["number"]).columns
negative_values = df[(df[numeric_cols] < 0).any(axis=1)]
if not negative_values.empty:
    negative_values.to_csv(f"{qa_folder}/negative_values.csv", index=False)
    print(f"⚠️  Found {len(negative_values)} rows with negative values.")
else:
    print("✅ No negative values found.")

# === Step 5: Check for High Trips Per Household ===
# (Let's flag anything over 10 trips per household for HBW, HBS, HBO)
df["TripsPerHH"] = (df["HBWP"] + df["HBSP"] + df["HBOP"]) / df["TAZ_ID"].replace(0, 1)
high_trips = df[df["TripsPerHH"] > 10]
if not high_trips.empty:
    high_trips.to_csv(f"{qa_folder}/high_trips_per_hh.csv", index=False)
    print(f"⚠️  Found {len(high_trips)} TAZs with unusually high trips per household.")
else:
    print("✅ Trips per household are within expected ranges.")

print("✅ QA checks complete.")
