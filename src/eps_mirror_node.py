#!/usr/bin/env python3
# ------------------------------------------------------------
#  mirror_node v2  (26-11-2025)
#  Developed by Team BOB (EPS Project) - HYOJUN CHOI
# ------------------------------------------------------------
#  Purpose:
#    - Receive trajectories from BOTH:
#        (1) MoveIt  : /display_planned_path (DisplayTrajectory)
#        (2) Terminal: /eps_arm/cmd (JointTrajectory)
#
#    - Normalize joint names:
#         Simulation : arm_0_joint_X
#         Real robot : joint_X
#
#    - Publish to:
#         Simulation : /r100_0000/arm_0_joint_trajectory_controller/joint_trajectory
#         Real robot : /joint_trajectory_controller/joint_trajectory
# ------------------------------------------------------------

import rclpy
from rclpy.node import Node
from moveit_msgs.msg import DisplayTrajectory
from trajectory_msgs.msg import JointTrajectory


class MirrorNode(Node):
    def __init__(self):
        super().__init__('mirror_node')

        # Parameters
        self.declare_parameter('display_topic', '/display_planned_path')
        self.declare_parameter('cmd_topic', '/eps_arm/cmd')
        self.declare_parameter(
            'sim_topic',
            '/r100_0000/arm_0_joint_trajectory_controller/joint_trajectory'
        )
        self.declare_parameter(
            'real_topic',
            '/joint_trajectory_controller/joint_trajectory'
        )

        # Load parameters
        display_topic = self.get_parameter('display_topic').get_parameter_value().string_value
        cmd_topic = self.get_parameter('cmd_topic').get_parameter_value().string_value
        sim_topic = self.get_parameter('sim_topic').get_parameter_value().string_value
        real_topic = self.get_parameter('real_topic').get_parameter_value().string_value

        self.get_logger().info(f'Display: {display_topic}')
        self.get_logger().info(f'CMD    : {cmd_topic}')
        self.get_logger().info(f'SIM    : {sim_topic}')
        self.get_logger().info(f'REAL   : {real_topic}')

        # Subscribers
        self.sub_display = self.create_subscription(
            DisplayTrajectory,
            display_topic,
            self.cb_display,
            10
        )

        # Subscribe terminal JointTrajectory commands
        self.sub_cmd = self.create_subscription(
            JointTrajectory,
            cmd_topic,
            self.cb_cmd,
            10
        )

        # Publishers
        self.pub_sim = self.create_publisher(JointTrajectory, sim_topic, 10)
        self.pub_real = self.create_publisher(JointTrajectory, real_topic, 10)

        self.get_logger().info('MirrorNode v2 started.')

    def normalize_and_publish(self, jt_in: JointTrajectory, source: str):
        # Basic checks
        if not jt_in.joint_names:
            self.get_logger().warn(f'[{source}] Empty joint_names')
            return
        if not jt_in.points:
            self.get_logger().warn(f'[{source}] Empty trajectory points')
            return

        # ---- Simulation message (with arm_0_ prefix) ----
        sim_msg = JointTrajectory()
        sim_msg.header = jt_in.header
        sim_msg.points = jt_in.points
        sim_msg.joint_names = []
        for name in jt_in.joint_names:
            if name.startswith('arm_0_'):
                sim_msg.joint_names.append(name)
            else:
                sim_msg.joint_names.append('arm_0_' + name)

        self.pub_sim.publish(sim_msg)

        # ---- Real robot message (without prefix) ----
        real_msg = JointTrajectory()
        real_msg.header = jt_in.header
        real_msg.points = jt_in.points
        # Strip 'arm_0_' prefix if present (hardware expects bare joint names)
        real_msg.joint_names = [
            n[len('arm_0_'):] if n.startswith('arm_0_') else n 
            for n in sim_msg.joint_names
        ]       

        self.pub_real.publish(real_msg)

        self.get_logger().info(
            f'[{source}] Published {len(sim_msg.points)} points to sim + real'
        )

    # MoveIt callback
    def cb_display(self, msg: DisplayTrajectory):
        if not msg.trajectory:
            self.get_logger().warn('[moveit] Empty DisplayTrajectory')
            return
        jt = msg.trajectory[0].joint_trajectory
        self.normalize_and_publish(jt, 'moveit')

    # Terminal callback
    def cb_cmd(self, msg: JointTrajectory):
        self.normalize_and_publish(msg, 'cmd')


def main(args=None):
    rclpy.init(args=args)
    node = MirrorNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
