# Gian Fernandez 10/2/26
# Script for optimizing power analysis measurements using jtop

from jtop import jtop
from datetime import datetime
import csv
import time

output_file = "jetson_log.csv"
interval = 15 # Time between logs in seconds
duration = 60 # in seconds
start_time = time.monotonic()

try:
    with jtop() as jetson:

        # Wait for first measurement
        if jetson.ok():

            with open(output_file, "w", newline="") as csvfile:

                fieldnames = [
                    "Time",
                    "VDD_GPU_SOC-IN_VOLTAGE_mW",
                    "VDD_GPU_SOC-IN_CURRENT_mA",
                    "VDD_GPU_SOC-IN_POWER_mW",
                    "VDD_GPU_SOC-AVG_POWER_mW",
                    "GPU_SHARED_MEMORY_MB"
                ]

                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                while jetson.ok():

                    if time.monotonic() - start_time >= duration:
                        print("20-minute loggin period complete.")
                        break

                    # Accessing the VDD_GPU_SOC power rail
                    gpu_rail = jetson.power["rail"]["VDD_GPU_SOC"]

                    # Obtaining shared memory of GPU
                    gpu_memory = jetson.memory["RAM"]["shared"] / 1024

                    row = {
                        "Time": datetime.now(),

                        # millivolts
                        "VDD_GPU_SOC-IN_VOLTAGE_mW":
                            gpu_rail["volt"],

                        # milliamps
                        "VDD_GPU_SOC-IN_CURRENT_mA":
                            gpu_rail["curr"],

                        # milliwatts
                        "VDD_GPU_SOC-IN_POWER_mW":
                            gpu_rail["power"],

                        # milliwatts
                        "VDD_GPU_SOC-AVG_POWER_mW":
                            gpu_rail["avg"],

                        # megabytes
                        "GPU_SHARED_MEMORY_MB":
                            gpu_memory
                    }   

                    # Immediately write data to disk
                    writer.writerow(row)
                    csvfile.flush()
                    # Adjust sampling rate/measurement frequency using time delay
                    time.sleep(interval)

except KeyboardInterrupt:
    print("\nLogging stopped by user.")
except Exception as e:
    print(f"\nAn error occured: {e}")