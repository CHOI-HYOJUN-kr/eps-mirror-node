"""Behavior checks without ROS2 or a connected robot."""
from copy import deepcopy
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from eps_mirror.routing import route_trajectory


def trajectory():
    return NS(
        header=NS(stamp=NS(sec=0, nanosec=0), frame_id=""),
        joint_names=[f"joint_{i}" for i in range(1, 8)],
        points=[NS(positions=[float(i) for i in range(7)], velocities=[],
                   accelerations=[], effort=[], time_from_start=NS(sec=t, nanosec=0))
                for t in (0, 1)],
    )


class RoutingTests(unittest.TestCase):
    def test_values_order_and_time_preserved_with_independent_copies(self):
        value = trajectory()
        value.joint_names.reverse()
        original = deepcopy(value)
        sim, real = route_trajectory(value)
        self.assertEqual(real.joint_names, original.joint_names)
        self.assertEqual(sim.joint_names, ["arm_0_" + n for n in original.joint_names])
        self.assertEqual(real.points, original.points)
        self.assertEqual(sim.header, original.header)
        sim.points[0].positions[0] = 999
        self.assertEqual(value, original)
        self.assertEqual(real, original)

    def test_prefixed_input_does_not_double_prefix(self):
        value = trajectory()
        value.joint_names = ["arm_0_" + n for n in value.joint_names]
        sim, real = route_trajectory(value)
        self.assertEqual(sim.joint_names, value.joint_names)
        self.assertEqual(real.joint_names[0], "joint_1")

    def test_invalid_inputs_rejected(self):
        mutations = {
            "empty": lambda t: t.points.clear(),
            "unknown": lambda t: t.joint_names.__setitem__(0, "gripper"),
            "duplicate": lambda t: t.joint_names.__setitem__(0, "joint_2"),
            "normalized_duplicate": lambda t: t.joint_names.__setitem__(0, "arm_0_joint_2"),
            "position_count": lambda t: t.points[0].positions.pop(),
            "nan": lambda t: t.points[0].positions.__setitem__(0, float("nan")),
            "inf": lambda t: t.points[0].positions.__setitem__(0, float("inf")),
            "velocity_count": lambda t: t.points[0].velocities.append(0),
            "negative_time": lambda t: setattr(t.points[0].time_from_start, "sec", -1),
            "nonmonotonic_time": lambda t: setattr(t.points[1].time_from_start, "sec", 0),
            "bad_nanosecond": lambda t: setattr(t.points[0].time_from_start, "nanosec", 1_000_000_000),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                value = trajectory()
                mutate(value)
                with self.assertRaises(ValueError):
                    route_trajectory(value)


if __name__ == "__main__":
    unittest.main()
