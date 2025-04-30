import pandas as pd
import os

print("🚗 QA Dashboard Starting...")

# === Step 1: Read Panda Output ===
input_path = "outputs/panda.csv"
df = pd.read_csv(input_path)

# === Step 2: Create QA Output Folder (if needed) ===
qa_folder = "outputs/qa"
os.makedirs(qa_folder, exist_ok=True)

# === Step 3: Basic Summaries ===
summary = []

summary.append(f"Total TAZs analyzed: {len(df)}")
summary.append("")

for field in ["HBWP", "HBWA", "HBSP", "HBSA", "HBOP", "HBOA", "RECP", "RECA"]:
    if field in df.columns:
        summary.append(f"--- {field} ---")
        summary.append(f"Min: {df[field].min():,.2f}")
        summary.append(f"Max: {df[field].max():,.2f}")
        summary.append(f"Mean: {df[field].mean():,.2f}")
        summary.append(f"Sum: {df[field].sum():,.2f}")
        summary.append("")

# === Step 4: Find Suspiciously High Trips (Simple Rule) ===
high_threshold = 10000  # very high total trips
df["TotalTrips"] = df[["HBWP", "HBSP", "HBOP", "RECP"]].sum(axis=1)
high_trips = df[df["TotalTrips"] > high_threshold]

if not high_trips.empty:
    summary.append(f"⚠️ Found {len(high_trips)} TAZs with TotalTrips > {high_threshold} trips.")
else:
    summary.append("✅ No TAZs with suspiciously high total trips.")

# === Step 5: Print and Save Summary ===
summary_text = "\n".join(summary)
print(summary_text)

# Save to file
output_file = os.path.join(qa_folder, "qa_summary.txt")
with open(output_file, "w", encoding="utf-8") as f:
    f.write(summary_text)

print(f"\n✅ QA Dashboard Completed. Summary saved to {output_file}")
