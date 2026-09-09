"""ROS-independent validation added in September 2026, based on EPS v2 routing.

Names are normalized; joint order, units, trajectory values and timestamps
are preserved. These checks are not joint-limit or collision validation.
"""
from copy import deepcopy
import math

PREFIX = "arm_0_"
EXPECTED = frozenset(f"joint_{i}" for i in range(1, 8))


def route_trajectory(trajectory):
    """Return independent (simulation, real) copies, or raise ValueError."""
    names = list(trajectory.joint_names)
    bare = [name[len(PREFIX):] if name.startswith(PREFIX) else name for name in names]
    if len(bare) != 7 or len(set(bare)) != 7 or set(bare) != EXPECTED:
        raise ValueError("Expected exactly joint_1..joint_7, with optional arm_0_ prefix")
    if not trajectory.points:
        raise ValueError("Trajectory contains no points")
    previous_ns = -1
    for point in trajectory.points:
        if len(point.positions) != 7:
            raise ValueError("Every point must contain seven positions")
        for field in ("positions", "velocities", "accelerations", "effort"):
            values = getattr(point, field)
            if len(values) not in (0, 7):
                raise ValueError(f"{field} length does not match joint_names")
            if any(not math.isfinite(value) for value in values):
                raise ValueError(f"Non-finite value in {field}")
        duration = point.time_from_start
        if duration.sec < 0 or not 0 <= duration.nanosec < 1_000_000_000:
            raise ValueError("Invalid time_from_start")
        current_ns = duration.sec * 1_000_000_000 + duration.nanosec
        if current_ns <= previous_ns:
            raise ValueError("time_from_start must increase strictly")
        previous_ns = current_ns
    simulation, real = deepcopy(trajectory), deepcopy(trajectory)
    simulation.joint_names = [PREFIX + name for name in bare]
    real.joint_names = bare
    return simulation, real
