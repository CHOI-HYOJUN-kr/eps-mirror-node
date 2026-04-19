#!/usr/bin/env python3
# ------------------------------------------------------------
#  Created: 20-11-2025
#  Author: Team BOB
#
#  JointMirror Node — Detailed Technical Concept
#  ---------------------------------------------------------
#  Overview:
#    The JointMirror node acts as a trajectory routing layer between a single
#    input command topic and two independent robot systems:
#       (1) Gazebo simulation of the Kinova Gen3 arm
#       (2) Physical Kinova Gen3 hardware
#
#    It enables unified control by consuming one JointTrajectory message and
#    re-publishing it to both robots with the necessary transformations.
#
#  Core Concept:
#    Both the simulation and the real robot operate under ROS2 and receive
#    arm motion through a JointTrajectory message. However:
#
#      • Simulation joint names include prefix:      "arm_0_joint_x"
#      • Real robot joint names DO NOT include it:   "joint_x"
#
#    This mismatch means a trajectory produced by MoveIt or a custom controller
#    can work for simulation but fail for the real robot unless adjusted.
#
#    The JointMirror node solves this by:
#      - Passing the message unchanged to the simulation controller.
#      - Removing the required joint name prefix before sending to hardware.
#
#    As a result, developers only need to publish ONCE to a unified topic,
#    guaranteeing synchronized behavior.
#
#  Why this is necessary (EPS Project Context):
#    The EPS setup uses:
#       • Gazebo-based Kinova Gen3 model for algorithm testing
#       • Real Kinova Gen3 arm for physical validation
#
#    To ensure consistent testing conditions and reproducibility, both systems
#    must execute identical trajectories. This node ensures:
#       - Software stack outputs the same motion to both robots
#       - No need to manually modify trajectories per system
#       - Reduced risk of inconsistent behavior between simulation and hardware
#
#  Message Flow Summary:
#      [MoveIt/Script/User Command]
#                 ↓
#          /eps_arm/cmd (JointTrajectory)
#                 ↓  (subscribed here)
#        ┌───────────────────────────────────┐
#        │        JointMirror Node           │
#        └───────────────────────────────────┘
#            ↓ unchanged          ↓ prefix removed
#       /sim trajectory        /real trajectory
#
#  This architecture is especially useful for:
#       - simultaneous testing
#       - side-by-side comparison
#       - unified control pipeline
#       - demo automation
# ------------------------------------------------------------

import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory


class JointMirror(Node):
    def __init__(self):
        super().__init__('joint_mirror')

        # --------------------------------------------------------
        # Topic configuration
        #
        # cmd_topic:
        #   Unified command input for both robots.
        #   MoveIt scripts, teleop, or custom controllers
        #   publish their JointTrajectory here.
        #
        # sim_topic:
        #   Gazebo's ros2_control controller input for the simulated arm.
        #
        # real_topic:
        #   ros2_control controller input for the physical Kinova Gen3.
        #
        # These default values match the EPS project environment but
        # can be overridden via launch files or CLI parameters.
        # --------------------------------------------------------
        self.declare_parameter('cmd_topic', '/eps_arm/cmd')
        self.declare_parameter(
            'sim_topic',
            '/r100_0000/arm_0_joint_trajectory_controller/joint_trajectory'
        )
        self.declare_parameter(
            'real_topic',
            '/joint_trajectory_controller/joint_trajectory'
        )

        # Load parameter values
        cmd_topic = self.get_parameter('cmd_topic').get_parameter_value().string_value
        sim_topic = self.get_parameter('sim_topic').get_parameter_value().string_value
        real_topic = self.get_parameter('real_topic').get_parameter_value().string_value

        # Log active settings
        self.get_logger().info(f'CMD  topic : {cmd_topic}')
        self.get_logger().info(f'SIM  topic : {sim_topic}')
        self.get_logger().info(f'REAL topic : {real_topic}')

        # Subscriber for unified input trajectory
        self.sub = self.create_subscription(
            JointTrajectory,
            cmd_topic,
            self.cb_cmd,
            10
        )

        # Publishers for simulation + real robot
        self.pub_sim = self.create_publisher(JointTrajectory, sim_topic, 10)
        self.pub_real = self.create_publisher(JointTrajectory, real_topic, 10)

    def cb_cmd(self, msg: JointTrajectory):
        """
        Callback for incoming JointTrajectory commands.

        Processing steps:
          (A) Mirror to Gazebo (no modification)
              - Gazebo’s controller accepts joint names with the prefix.
              - Message is published exactly as received.

          (B) Mirror to the real Kinova Gen3 (requires joint name adjustment)
              - The hardware controller expects joint names without "arm_0_".
              - A parallel JointTrajectory message is created.
              - Header and trajectory points are copied.
              - Joint names are processed to strip the prefix.
                Example:
                    "arm_0_joint_2" → "joint_2"

        This ensures the real robot receives a valid command while the
        simulated version receives the original message unchanged.
        """

        # (A) Publish original trajectory to Gazebo
        self.pub_sim.publish(msg)

        # (B) Build the modified trajectory for real Kinova hardware
        real_msg = JointTrajectory()
        real_msg.header = msg.header
        real_msg.points = msg.points

        # Remove prefix for hardware compatibility
        real_msg.joint_names = [
            name.replace('arm_0_', '') for name in msg.joint_names
        ]

        self.pub_real.publish(real_msg)


def main():
    rclpy.init()
    node = JointMirror()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

