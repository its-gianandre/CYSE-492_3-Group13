# Gian Fernandez 10/2/26
# Script for optimizing power analysis measurements using jtop
# This script is able to log specific metrics related to the GPU and memory/RAM
# We are able to control the sampling rate, the length at which we want to capture/log data, and
# output all of this data into a .csv file

from jtop import jtop
from datetime import datetime
import csv
import time

output_file = "Moondream_poweranalysis_MAXN_noattack_10-2-26.csv"
interval = 30 # Time between logs in seconds
duration = 20 * 60 # Duration to log data in seconds
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
                    "GPU_SHARED_MEMORY_MB",
                    "USED_MEMORY_MB",
                    "TOTAL_MEMORY_MB"
                ]

                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                print(f"Beginning logging process for {duration//60} minutes")
                
                while jetson.ok():

                    if time.monotonic() - start_time >= duration:
                        print("Logging period complete. Check folder for .csv file")
                        break

                    # Accessing the VDD_GPU_SOC power rail
                    gpu_rail = jetson.power["rail"]["VDD_GPU_SOC"]

                    # Obtaining shared memory of GPU
                    gpu_memory = jetson.memory["RAM"]["shared"] / 1024
                    
                    # Access RAM statistics
                    ram = jetson.memory["RAM"]
                    # Convert from KB to MB
                    total_memory = ram["tot"]/1024
                    used_memory = ram["used"]/1024

                    row = {
                        "Time": datetime.now(),

                        # Measuring GPU voltage in milliwatts
                        "VDD_GPU_SOC-IN_VOLTAGE_mW":
                            gpu_rail["volt"],

                        # Measuring GPU current in milliamps
                        "VDD_GPU_SOC-IN_CURRENT_mA":
                            gpu_rail["curr"],

                        # Measuring GPU power in milliwatts
                        "VDD_GPU_SOC-IN_POWER_mW":
                            gpu_rail["power"],

                        # Measuring average GPU power in milliwatts
                        "VDD_GPU_SOC-AVG_POWER_mW":
                            gpu_rail["avg"],

                        # GPU shared memory in megabytes
                        "GPU_SHARED_MEMORY_MB":
                            gpu_memory,
                        
                        # Measuring memory in use from RAM
                        "USED_MEMORY_MB":
                            used_memory,
                            
                        # Total memory in RAM for reference
                        "TOTAL_MEMORY_MB":
                            total_memory
                        
                    }   

                    # Immediately write data to disk
                    writer.writerow(row)
                    csvfile.flush()
                    # Adjust sampling rate/measurement frequency using time delay (in seconds)
                    time.sleep(interval)

except KeyboardInterrupt:
    print("\nLogging stopped by user.")
except Exception as e:
    print(f"\nAn error occurred: {e}")
