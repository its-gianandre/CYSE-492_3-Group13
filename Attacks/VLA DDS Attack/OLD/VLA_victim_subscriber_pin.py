# Copyright 2016 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Modified by CYSE 492 Group 13
# 11/5/26

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from std_msgs.msg import String
import subprocess #modified
import sys #modified


class Listener(Node):

    def __init__(self, attack):
        super().__init__('listener')
        
        self.sub = self.create_subscription(String, 'chatter', self.chatter_callback, 10) #modified

    def chatter_callback(self, msg):
        #Message To Confirm Attack Packet was recieved below:
        self.get_logger().info('I heard: [%s], Executing Attack' % msg.data) #modified

        #Attack execution bellow:
        attack_cmd = 'cd ~/Documents/week7/bella && ./gpu_cache_thrash pin 90 1300'
        subprocess.Popen(attack_cmd, shell=True)

        #Message To Confirm Attack executed below:
        self.get_logger().info('Executed the attack, killing node...\n')
        quit() #stopping program altogether


def main(args=None):
    rclpy.init(args=args)

    node = Listener()

    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
