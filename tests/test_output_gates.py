"""Exercise the real wrapper with in-memory ROS substitutes, not a ROS test."""
import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace as NS
import unittest
from unittest.mock import patch
from test_routing import trajectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class Publisher:
    def __init__(self): self.messages = []
    def publish(self, message): self.messages.append(message)


class FakeNode:
    overrides = {}
    def __init__(self, name): self.parameters = {}
    def declare_parameter(self, key, default): self.parameters[key] = self.overrides.get(key, default)
    def get_parameter(self, key): return NS(value=self.parameters[key])
    def create_publisher(self, *args): return Publisher()
    def create_subscription(self, *args): return args
    def get_logger(self): return NS(info=lambda _: None, warn=lambda _: None)


stubs = {name: ModuleType(name) for name in
         ("rclpy", "rclpy.node", "moveit_msgs", "moveit_msgs.msg", "trajectory_msgs", "trajectory_msgs.msg")}
stubs["rclpy.node"].Node = FakeNode
stubs["moveit_msgs.msg"].DisplayTrajectory = NS
stubs["trajectory_msgs.msg"].JointTrajectory = NS
with patch.dict(sys.modules, stubs):
    MirrorNode = importlib.import_module("eps_mirror.mirror_node").MirrorNode


class OutputGateTests(unittest.TestCase):
    def setUp(self): FakeNode.overrides = {}

    def test_default_has_no_real_publisher(self):
        node = MirrorNode()
        node.cb_cmd(trajectory())
        self.assertIsNone(node.pub_real)
        self.assertEqual(len(node.pub_sim.messages), 1)

    def test_real_command_opt_in_does_not_enable_display_motion(self):
        FakeNode.overrides = {"enable_real": True}
        node = MirrorNode()
        node.cb_display(NS(trajectory=[NS(joint_trajectory=trajectory())]))
        self.assertEqual(len(node.pub_real.messages), 0)
        node.cb_cmd(trajectory())
        self.assertEqual(len(node.pub_real.messages), 1)

    def test_display_requires_additional_opt_in(self):
        FakeNode.overrides = {"enable_real": True, "allow_display_to_real": True, "enable_sim": False}
        node = MirrorNode()
        node.cb_display(NS(trajectory=[NS(joint_trajectory=trajectory())]))
        self.assertIsNone(node.pub_sim)
        self.assertEqual(len(node.pub_real.messages), 1)

    def test_invalid_input_reaches_neither_output(self):
        FakeNode.overrides = {"enable_real": True}
        node = MirrorNode()
        value = trajectory()
        value.points[0].positions[0] = float("nan")
        node.cb_cmd(value)
        node.cb_display(NS(trajectory=[]))
        self.assertEqual(node.pub_sim.messages, [])
        self.assertEqual(node.pub_real.messages, [])

    def test_feedback_configuration_rejected(self):
        FakeNode.overrides = {"sim_topic": "/eps_arm/cmd"}
        with self.assertRaises(ValueError): MirrorNode()


if __name__ == "__main__": unittest.main()
