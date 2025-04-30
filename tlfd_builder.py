import pandas as pd
import os

print("Building Gravity Friction Factors (TLFDs)...")

# === Step 1: Define Distance Bins (in miles) ===
dist_bins = ["0–1", "1–2", "2–3", "3–5", "5–10", "10–20", "20–30", "30–40", "40+"]

# === Step 2: Define Friction Factors by Trip Purpose ===
# These are placeholder decay curves — calibrate later based on observed data
tlfd_data = {
    "DIST_BIN_MI": dist_bins,
    "HBW":  [1.00, 0.95, 0.85, 0.75, 0.60, 0.40, 0.20, 0.08, 0.01],
    "HBO":  [1.00, 0.92, 0.80, 0.65, 0.40, 0.20, 0.08, 0.02, 0.00],
    "HBS":  [1.00, 0.90, 0.78, 0.60, 0.35, 0.15, 0.05, 0.01, 0.00],
}

df = pd.DataFrame(tlfd_data)

# === Step 3: Basic QA Check ===
for col in ["HBW", "HBO", "HBS"]:
    if not df[col].is_monotonic_decreasing:
        print(f"⚠️ WARNING: Friction curve for {col} is not strictly decreasing.")
    else:
        print(f"✅ Friction curve for {col} passes monotonic check.")

# === Step 4: Save to Outputs ===
output_folder = "outputs"
os.makedirs(output_folder, exist_ok=True)

output_path = os.path.join(output_folder, "gravity_friction_factors.csv")
df.to_csv(output_path, index=False)

print(f"\n✅ TLFD table saved to: {output_path}")

