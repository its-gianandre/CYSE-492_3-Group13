
# NANO VERSION: Orin Nano reports power on different rails than AGX Orin.
# AGX Orin has separate VDD_GPU_SOC and VDD_CPU_CV rails (GPU isolated from CPU).
# Orin Nano combines them into one VDD_CPU_GPU_CV rail -- there is no way to read
# GPU-only power on this board. Column names below are renamed accordingly so it's
# clear this is combined CPU+GPU power, not GPU-only like the Orin's data.

from jtop import jtop
from datetime import datetime
import csv
import os
import time

output_file = "jetson_log.csv"
interval = float(os.environ.get("JTOP_INTERVAL", "15"))  # Time between logs in seconds
duration = float(os.environ.get("JTOP_DURATION", "60"))  # in seconds
start_time = time.monotonic()

try:
    with jtop() as jetson:

        # Wait for first measurement
        if jetson.ok():

            with open(output_file, "w", newline="") as csvfile:

                fieldnames = [
                    "Time",
                    "VDD_CPU_GPU_CV-IN_VOLTAGE_mW",
                    "VDD_CPU_GPU_CV-IN_CURRENT_mA",
                    "VDD_CPU_GPU_CV-IN_POWER_mW",
                    "VDD_CPU_GPU_CV-AVG_POWER_mW",
                    "GPU_SHARED_MEMORY_MB"
                ]

                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                while jetson.ok():

                    if time.monotonic() - start_time >= duration:
                        print(f"{duration:.0f}-second logging period complete.")
                        break

                    # Accessing the VDD_CPU_GPU_CV power rail -- this is the combined
                    # CPU+GPU rail on Orin Nano (no separate GPU-only rail exists here,
                    # unlike AGX Orin's VDD_GPU_SOC).
                    rail = jetson.power["rail"]["VDD_CPU_GPU_CV"]

                    # Obtaining shared memory of GPU
                    gpu_memory = jetson.memory["RAM"]["shared"] / 1024

                    row = {
                        "Time": datetime.now(),

                        # millivolts
                        "VDD_CPU_GPU_CV-IN_VOLTAGE_mW":
                            rail["volt"],

                        # milliamps
                        "VDD_CPU_GPU_CV-IN_CURRENT_mA":
                            rail["curr"],

                        # milliwatts
                        "VDD_CPU_GPU_CV-IN_POWER_mW":
                            rail["power"],

                        # milliwatts
                        "VDD_CPU_GPU_CV-AVG_POWER_mW":
                            rail["avg"],

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
