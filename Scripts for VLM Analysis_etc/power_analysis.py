# Gian Fernandez 10/2/26
# Script for optimizing power analysis measurements using jtop
# This script is able to log specific metrics related to the GPU and memory/RAM
# We are able to control the sampling rate, the length at which we want to capture/log data, and
# output all of this data into a .csv file

#modified by shanti 10/9/2026
import sys

from jtop import jtop
from datetime import datetime
import csv
import time

try:
    args_len = len(sys.argv)
    file_name = ''.join(sys.argv[-1])
    file_extension = file_name.split('.')[-1]

    #check to make sure all arguments there
    if (args_len < 4 or (file_extension != 'csv')):
        print("\n\nERROR: Argument should include the sample rate, duration and the .csv name\nFormat: python3 power_analysis.py sample_rate duration output_file.csv\nEx: python3 power_analysis.py 30 20 output.csv")
        print('Sample rate: in seconds')
        print('duration: in minutes')
        print('the .csv name: test.csv', end='\n\n')

    else:
        output_file = sys.argv[-1]
        interval = float(sys.argv[1])
        duration = float(sys.argv[2]) * 60
        start_time = time.monotonic()

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
                        "GPU_SHARED_MEMORY_GB",
                        "USED_MEMORY_GB",
                        "TOTAL_MEMORY_GB"
                    ]

                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    print(f"Beginning logging process for {duration/60:.2f} minute(s)")
                    
                    while jetson.ok():

                        if time.monotonic() - start_time >= duration:
                            print("Logging period complete. Check folder for .csv file")
                            break

                        # Accessing the VDD_GPU_SOC power rail
                        gpu_rail = jetson.power["rail"]["VDD_GPU_SOC"]

                        # Obtaining shared memory of GPU
                        gpu_memory = jetson.memory["RAM"]["shared"] / 1048576
                        
                        # Access RAM statistics
                        ram = jetson.memory["RAM"]
                        # Convert from KB to GB
                        total_memory = ram["tot"]/1048576
                        used_memory = ram["used"]/1048576

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

                            # GPU shared memory in gigabytes
                            "GPU_SHARED_MEMORY_GB":
                                gpu_memory,
                            
                            # Measuring memory in use from RAM
                            "USED_MEMORY_GB":
                                used_memory,
                                
                            # Total memory in RAM for reference
                            "TOTAL_MEMORY_GB":
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
