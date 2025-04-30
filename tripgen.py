import pandas as pd
import os

print("Trip Generation Script Starting...")

# === Step 1: Create trip generation data ===
# Replace this with your real generation model later
trip_data = {
    "TAZ_ID": [101, 102, 103, 104],
    "PRODUCTIONS": [2000, 1500, 1100, 1800],
    "ATTRACTIONS": [2100, 1400, 1000, 1900]
}
panda_df = pd.DataFrame(trip_data)

# === Step 2: Load Special Generators ===
special_path = "outputs/special_generators.csv"
if os.path.exists(special_path):
    specials = pd.read_csv(special_path)
    print(f"✅ Loaded {len(specials)} special generators.")

    for _, row in specials.iterrows():
        taz = row['TAZ_ID']
        trips = row['DAILY_TRIPS']

        if taz in panda_df['TAZ_ID'].values:
            # Add to existing TAZ
            panda_df.loc[panda_df['TAZ_ID'] == taz, 'ATTRACTIONS'] += trips
            print(f"  ➕ Added {trips} trips to existing TAZ {taz}")
        else:
            # Add new TAZ row
            new_row = {
                "TAZ_ID": taz,
                "PRODUCTIONS": 0,
                "ATTRACTIONS": trips
            }
            panda_df = pd.concat([panda_df, pd.DataFrame([new_row])], ignore_index=True)
            print(f"  🆕 Added new TAZ {taz} with {trips} attraction trips")
else:
    print("⚠️ No special_generators.csv found — skipping merge.")

# === Step 3: Save updated PANDA ===
output_folder = "outputs"
os.makedirs(output_folder, exist_ok=True)
output_path = os.path.join(output_folder, "panda_with_specials.csv")
panda_df.to_csv(output_path, index=False)

print(f"✅ Trip generation with specials completed. File saved to {output_path}")
