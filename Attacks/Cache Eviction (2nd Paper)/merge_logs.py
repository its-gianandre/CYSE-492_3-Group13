# merges one run's power CSV (from the jtop script) and latency CSV (from vlm_webcam.py)
# needs: pip3 install pandas --break-system-packages
#
# Usage:
#   python3 merge_logs.py <power_csv> <latency_csv> <output_csv>

import sys
import pandas as pd

if len(sys.argv) != 4:
    print("Usage: python3 merge_logs.py <power_csv> <latency_csv> <output_csv>")
    sys.exit(1)

power_path, latency_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]

power_df = pd.read_csv(power_path)
power_df["Time"] = pd.to_datetime(power_df["Time"])
power_df = power_df.sort_values("Time")

latency_df = pd.read_csv(latency_path)
latency_df["time"] = pd.to_datetime(latency_df["time"])
latency_df = latency_df.sort_values("time")

# merge_asof matches each power row to the nearest latency row in time
# direction="nearest" picks whichever latency reading is closest in either direction
# instead of requiring the latency sample to come before or after the power sample.
merged = pd.merge_asof(
    power_df, latency_df,
    left_on="Time", right_on="time",
    direction="nearest",
    tolerance=pd.Timedelta("20s"),  # if no latency reading is within 20s, leave it blank
                                     # rather than matching something misleadingly far away
)

merged = merged.drop(columns=["time"])  # redundant with Time now that the join is done
merged.to_csv(out_path, index=False)

print(f"Merged {len(power_df)} power rows with {len(latency_df)} latency rows -> {out_path}")
unmatched = merged["latency_s"].isna().sum()
if unmatched:
    print(f"Note: {unmatched} power row(s) had no latency reading within 20s and were left blank.")
