#!/usr/bin/env python3
"""EPS v2-derived ROS2 wrapper. September 2026 maintenance, not hardware-tested.

Real output requires enable_real:=true. Display messages reach real output
only with the additional allow_display_to_real:=true opt-in.
"""
import rclpy
from rclpy.node import Node
from moveit_msgs.msg import DisplayTrajectory
from trajectory_msgs.msg import JointTrajectory
from .routing import route_trajectory


class MirrorNode(Node):
    def __init__(self):
        super().__init__("mirror_node")
        defaults = {
            "display_topic": "/display_planned_path",
            "cmd_topic": "/eps_arm/cmd",
            "sim_topic": "/r100_0000/arm_0_joint_trajectory_controller/joint_trajectory",
            "real_topic": "/joint_trajectory_controller/joint_trajectory",
            "enable_sim": True,
            "enable_real": False,
            "allow_display_to_real": False,
        }
        for key, value in defaults.items():
            self.declare_parameter(key, value)
        params = {key: self.get_parameter(key).value for key in defaults}
        for key in ("enable_sim", "enable_real", "allow_display_to_real"):
            if not isinstance(params[key], bool):
                raise ValueError(f"{key} must be a boolean")
        topics = [params[key] for key in ("display_topic", "cmd_topic", "sim_topic", "real_topic")]
        if any(not isinstance(topic, str) or not topic.startswith("/") for topic in topics):
            raise ValueError("Use non-empty absolute topic names")
        if len(set(topics)) != len(topics):
            raise ValueError("Input and output topics must be distinct to avoid feedback")
        self.allow_display_to_real = params["allow_display_to_real"]
        self.pub_sim = self.create_publisher(JointTrajectory, params["sim_topic"], 10) if params["enable_sim"] else None
        self.pub_real = self.create_publisher(JointTrajectory, params["real_topic"], 10) if params["enable_real"] else None
        self.sub_display = self.create_subscription(DisplayTrajectory, params["display_topic"], self.cb_display, 10)
        self.sub_cmd = self.create_subscription(JointTrajectory, params["cmd_topic"], self.cb_cmd, 10)
        self.get_logger().info(f"Output enabled: sim={params['enable_sim']}, real={params['enable_real']}")

    def publish_trajectory(self, trajectory, source):
        try:
            simulation, real = route_trajectory(trajectory)
        except (ValueError, TypeError, AttributeError) as error:
            self.get_logger().warn(f"Rejected {source}: {error}")
            return
        if self.pub_sim is not None:
            self.pub_sim.publish(simulation)
        if self.pub_real is not None and (source == "command" or self.allow_display_to_real):
            self.pub_real.publish(real)

    def cb_display(self, message):
        if not message.trajectory:
            self.get_logger().warn("Rejected empty DisplayTrajectory")
            return
        if len(message.trajectory) > 1:
            self.get_logger().warn("Only trajectory[0] is routed; remaining segments are ignored")
        self.publish_trajectory(message.trajectory[0].joint_trajectory, "display")

    def cb_cmd(self, message):
        self.publish_trajectory(message, "command")


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = MirrorNode()
        rclpy.spin(node)
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
