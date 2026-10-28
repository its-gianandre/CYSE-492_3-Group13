# Combined power + latency logger for the SmolVLA/TurtleBot pipeline.
# Extends the original jetson_log.py (power-only) by also subscribing to
# /vla/predicted_action as a ROS2 node, so one script produces one CSV with
# both metrics already time-aligned -- no separate merge step needed.
#
# Usage (same env vars as the original jetson_log.py):
#   JTOP_INTERVAL=5 JTOP_DURATION=90 python3 jetson_log_vla.py
#
# Requires rclpy + sourcing ROS/the smolvla venv/the ros2_ws, same as inference_node itself
import csv
import os
import time
from datetime import datetime

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from jtop import jtop

output_file = "jetson_log_vla.csv"
interval = float(os.environ.get("JTOP_INTERVAL", "15"))
duration = float(os.environ.get("JTOP_DURATION", "60"))

# EDIT TO MATCH YOUR BOARD:
#   AGX Orin -> "VDD_GPU_SOC"
#   Orin Nano -> "VDD_CPU_GPU_CV"
POWER_RAIL = "VDD_GPU_SOC"


class VLAPowerLatencyLogger(Node):
    def __init__(self, writer, csvfile, jetson):
        super().__init__("vla_power_latency_logger")
        self.writer = writer
        self.csvfile = csvfile
        self.jetson = jetson

        self.prediction_count = 0
        self.last_prediction_time = None

        self.subscription = self.create_subscription(
            String, "/vla/predicted_action", self.on_prediction, 10
        )
         # Timer fires on the same interval as the original power-only script
        self.power_timer = self.create_timer(interval, self.on_power_tick)

        self.start_time = time.monotonic()
        self.shutdown_requested = False

    def on_prediction(self, msg):
        now = time.monotonic()
        self.prediction_count += 1

        # Time since the previous prediction -- this is your latency/period
        # metric, the same thing `ros2 topic hz` reports in aggregate, but
        # now logged per-event with a real timestamp attached.
        if self.last_prediction_time is not None:
            delta = now - self.last_prediction_time
        else:
            delta = None  # first prediction has no prior one to compare to

        self.last_prediction_time = now
        row = {
            "Time": datetime.now(),
            "row_type": "prediction",
            "prediction_number": self.prediction_count,
            "prediction_latency_s": delta,
            "predicted_action": msg.data,
            f"{POWER_RAIL}-IN_POWER_mW": "",
            "GPU_SHARED_MEMORY_MB": "",
        }
        self.writer.writerow(row)
        self.csvfile.flush()
        self.get_logger().info(f"Prediction #{self.prediction_count}: {msg.data} (delta={delta})")
    def on_power_tick(self):
        if time.monotonic() - self.start_time >= duration:
            self.get_logger().info(f"{duration:.0f}-second logging period complete.")
            self.shutdown_requested = True
            return

        if not self.jetson.ok():
            return

        rail = self.jetson.power["rail"][POWER_RAIL]
        gpu_memory = self.jetson.memory["RAM"]["shared"] / 1024

        row = {
            "Time": datetime.now(),
            "row_type": "power",
            "prediction_number": "",
            "prediction_latency_s": "",
            "predicted_action": "",
            f"{POWER_RAIL}-IN_POWER_mW": rail["power"],
            "GPU_SHARED_MEMORY_MB": gpu_memory,
        }
        self.writer.writerow(row)
        self.csvfile.flush()
      
def main():
    with jtop() as jetson:
        if not jetson.ok():
            print("jtop not ready -- aborting.")
            return

        with open(output_file, "w", newline="") as csvfile:
            fieldnames = [
                "Time",
                "row_type",
                "prediction_number",
                "prediction_latency_s",
                "predicted_action",
                f"{POWER_RAIL}-IN_POWER_mW",
                "GPU_SHARED_MEMORY_MB",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            rclpy.init()
            node = VLAPowerLatencyLogger(writer, csvfile, jetson)

            try:
                while rclpy.ok() and not node.shutdown_requested:
                    rclpy.spin_once(node, timeout_sec=0.5)
            except KeyboardInterrupt:
                print("\nLogging stopped by user.")
            finally:
                node.destroy_node()
                rclpy.shutdown()


if __name__ == "__main__":
    main()
