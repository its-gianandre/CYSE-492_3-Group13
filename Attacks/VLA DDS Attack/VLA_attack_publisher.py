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

#Modified by GMU CYSE-492 Group 13
#All credits to Original Authors mentioned above

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from std_msgs.msg import String

import sys #modified

class Talker(Node):

    def __init__(self, attack, duration, iterations):
        super().__init__('talker')
        self.i = 0
        self.pub = self.create_publisher(String, 'chatter', 10)
        timer_period = 1.0
        self.tmr = self.create_timer(timer_period, self.timer_callback)

        #below is our modifications
        if(attack != 'pin' or attack != 'scan'):
            print('\nSYNTAX: ros2 run vla_attack_pkg attack_publisher attack_name duration_time number_of_iterations')
            print("ERROR: attack parameter can only be \'pin\' or \'scan\'")
            quit()
        elif((len(duration.strip()) == 0) or (int(duration.strip()) <= 0)):
            print('\nSYNTAX: ros2 run vla_attack_pkg attack_publisher attack_name duration_time number_of_iterations')
            print('ERROR" duration parameter cannot be empty or <= \'0\'')
            quit()
        elif((len(iterations.strip() == 0)) or (int(iterations.strip()) <= 0)):
            print('\nSYNTAX: ros2 run vla_attack_pkg attack_publisher attack_name duration_time number_of_iterations')
            print('ERROR" iterations parameter cannot be empty or <= \'0\'')
            quit()


        self.attack = attack
        self.duration = int(duration)
        self.iterations = int(iterations)
        #end of modifications

    def timer_callback(self):
        msg = String()
        msg.data = f'Attack_Packet - {self.attack} {self.duration} {self.iterations}: {0}'.format(self.i) #modified
        self.i += 1
        self.get_logger().info(f'Sending Attack Packet to Execute the {self.attack} Attack with Duration: {self.duration} and Iterations: {self.iterations} Locally on AGX Turtlebot3: "{0}"'.format(msg.data)) #modified
        self.pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)

    node = Talker(attack=sys.argv[1], duration=sys.argv[2], iterations=sys.argv[3]) # modified

    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
