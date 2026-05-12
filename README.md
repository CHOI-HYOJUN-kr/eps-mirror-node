# Mobile Collaborative Robot

EPS Fall 2025 — Team BOB
ENIT, Tarbes, France · Commissioned by LGP Lab (UTTOP)

A ROS 2 Jazzy stack that integrates a Clearpath Ridgeback mobile base
and a Kinova Gen3 7-DOF arm, so that the same MoveIt 2 trajectory runs
on both the Gazebo simulation and the real robot at the same time.

![Demo](assets/eps_demo.gif)

## My Contribution (Hyojun Choi)

Responsible for the Kinova Gen3 side. Identified the joint name /
controller namespace mismatch between Gazebo (`arm_0_joint_X`) and the
real hardware (`joint_X`), led the team discussion that settled on a
custom-node approach, and designed the two-stage node architecture:

- **`kinova_mirror_node.py`** — first version; subscribes to a unified
  `/eps_arm/cmd` topic and re-publishes to both the sim and real
  controllers with the appropriate prefix handling.
- **`display_to_eps_cmd.py`** — bridge node that taps MoveIt's
  `/display_planned_path` output, normalizes joint names, and feeds the
  result into `/eps_arm/cmd`.
- **`eps_mirror_node.py`** (MirrorNode v2) — merged both functions into
  a single node, accepting either a `DisplayTrajectory` from MoveIt or
  a direct `JointTrajectory` from the terminal, then routing to sim and
  real simultaneously.

Also handled the `robot.yaml` crash diagnosis (component-by-component
removal to isolate the cause), wrote the unified launch files and the
Kinova connection bash script, and authored the Setup Guide in full.
The full reasoning, trade-offs, and step-by-step problem solving are
documented in [**TROUBLESHOOTING.md**](./TROUBLESHOOTING.md).

## Node Architecture

```
MoveIt (RViz Plan/Execute)          Terminal command
        ↓                                  ↓
/display_planned_path          /eps_arm/cmd (JointTrajectory)
        └──────────────┬───────────────────┘
                       ↓
               [ MirrorNode v2 ]
               (eps_mirror_node.py)
                  ↓           ↓
         Gazebo sim        Real Kinova Gen3
       (arm_0_joint_X)      (joint_X)
```

## Repository Layout

| Folder | Contents |
| --- | --- |
| `src/` | ROS 2 nodes: `eps_mirror_node.py` (MirrorNode v2), `display_to_eps_cmd.py` (bridge), `kinova_mirror_node.py` (JointMirror v1) |
| `launch/` | `eps_sim.launch.py` (simulation), `eps_kinova.launch.py` (real robot) |
| `scripts/` | `eps_kinova_connect.sh` — automates network config for real Kinova |
| `config/` | `robot.yaml` (Clearpath robot description) |
| `assets/` | `rosgraph(final).png`, `TF tree.pdf`, `eps_demo.gif` |
| `docs/` | Team-level reports (Final Document, Setup Guide, summary) |

## Environment

- ROS 2 Jazzy
- Gazebo (Clearpath simulation packages)
- MoveIt 2
- Kinova Kortex ROS 2 driver

## Run

```bash
# Simulation
ros2 launch eps_bringup eps_sim.launch.py

# Real Kinova
bash scripts/eps_kinova_connect.sh
ros2 launch eps_bringup eps_kinova.launch.py
```

## Project Period

2025-09-01 – 2025-12-18 · 30 ECTS · one semester
