#!/usr/bin/env python3
# ------------------------------------------------------------
#  Created: 24-11-2025
#  Author: Team BOB
#
#  DisplayToEpsCmd Node — Detailed Technical Concept
#  ---------------------------------------------------------
#  Overview:
#    This node bridges MoveIt's visualization output with the unified
#    command interface used in the EPS project.
#
#    In MoveIt, planned paths are typically published as
#      - moveit_msgs/DisplayTrajectory
#      - Topic: /display_planned_path
#
#    However, the actual robot controllers (simulation + real hardware)
#    expect plain JointTrajectory commands on control topics.
#
#    This node:
#      1) Listens to MoveIt's /display_planned_path topic.
#      2) Extracts the first RobotTrajectory's JointTrajectory.
#      3) Normalizes joint names by ensuring they have the "arm_0_" prefix.
#      4) Publishes the result as a standard JointTrajectory to /eps_arm/cmd.
#
#    The /eps_arm/cmd topic is then consumed by the JointMirror node, which:
#      - Sends the trajectory unchanged to Gazebo.
#      - Strips "arm_0_" prefix for the real Kinova Gen3 arm.
#
#  High-level pipeline:
#      MoveIt (Plan / Plan+Execute)
#           ↓
#      /display_planned_path (DisplayTrajectory)
#           ↓
#      [DisplayToEpsCmd Node]
#           ↓
#      /eps_arm/cmd (JointTrajectory)
#           ↓
#      [JointMirror Node]
#           ↓                     ↓
#   Gazebo simulated arm     Real Kinova Gen3
#
#  Purpose:
#    - Reuse MoveIt's planned trajectories directly for execution.
#    - Provide a clean, unified command topic for both simulation and hardware.
#    - Ensure consistent joint naming convention for downstream nodes.
# ------------------------------------------------------------

import rclpy
from rclpy.node import Node
from moveit_msgs.msg import DisplayTrajectory
from trajectory_msgs.msg import JointTrajectory


class DisplayToEpsCmd(Node):
    def __init__(self):
        super().__init__('display_to_eps_cmd')

        # --------------------------------------------------------
        # Subscriber:
        #   - Input: MoveIt's planned motion, used for visualization.
        #   - Type:  moveit_msgs/DisplayTrajectory
        #   - Topic: /display_planned_path
        #
        #   MoveIt publishes here whenever you press "Plan" or "Plan + Execute"
        #   in RViz. This contains one or more RobotTrajectory objects.
        # --------------------------------------------------------
        self.sub = self.create_subscription(
            DisplayTrajectory,
            '/display_planned_path',
            self.cb_display,
            10
        )

        # --------------------------------------------------------
        # Publisher:
        #   - Output: Plain JointTrajectory command compatible with
        #             the EPS unified control pipeline.
        #   - Type:   trajectory_msgs/JointTrajectory
        #   - Topic:  /eps_arm/cmd
        #
        #   This is the same topic that the JointMirror node listens to,
        #   which mirrors the command to:
        #       - Gazebo simulated controller
        #       - Real Kinova controller
        # --------------------------------------------------------
        self.pub = self.create_publisher(
            JointTrajectory,
            '/eps_arm/cmd',
            10
        )

        self.get_logger().info('DisplayToEpsCmd node started.')

    def cb_display(self, msg: DisplayTrajectory):
        """
        Callback for MoveIt's DisplayTrajectory messages.

        DisplayTrajectory structure (simplified):
          - msg.trajectory: list of RobotTrajectory
          - Each RobotTrajectory contains:
                robot_trajectory.joint_trajectory  (JointTrajectory)

        Processing steps:
          1. Validate that the trajectory list is not empty.
          2. Take the first RobotTrajectory as the planned path to execute.
          3. Extract its JointTrajectory.
          4. Create a new JointTrajectory:
               - Copy header (timing frame, stamp).
               - Copy trajectory points (positions, velocities, etc.).
               - Normalize joint names:
                    * If "arm_0_" prefix is missing, add it.
                    * This aligns with the naming used in Gazebo + mirror node.
          5. Publish the normalized JointTrajectory to /eps_arm/cmd.
        """

        # 1) Ensure there is at least one trajectory to process
        if not msg.trajectory:
            self.get_logger().warn('DisplayTrajectory has empty trajectory[]; nothing to convert.')
            return

        # 2) Extract the first RobotTrajectory's JointTrajectory
        jt = msg.trajectory[0].joint_trajectory

        # 3) Build a new JointTrajectory to send to /eps_arm/cmd
        out = JointTrajectory()
        out.header = jt.header    # preserve original timing/frame info
        out.points = jt.points    # reuse all the planned trajectory points

        # 4) Normalize joint names: ensure "arm_0_" prefix is present.
        #    - MoveIt configurations may use shorter names like "joint_1".
        #    - Gazebo + mirror_node expect "arm_0_joint_1".
        out.joint_names = []
        for name in jt.joint_names:
            if name.startswith('arm_0_'):
                out.joint_names.append(name)
            else:
                out.joint_names.append('arm_0_' + name)

        # 5) Publish converted trajectory into the unified EPS command topic
        self.pub.publish(out)

        self.get_logger().info(
            f'Published trajectory with {len(out.points)} points to /eps_arm/cmd'
        )


def main(args=None):
    rclpy.init(args=args)
    node = DisplayToEpsCmd()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

