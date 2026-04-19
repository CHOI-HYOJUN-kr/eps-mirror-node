# EPS Mirror Node — ROS2 Sim-to-Real Trajectory Mirroring

A ROS2 custom node developed during the **European Project Semester (EPS)** at LGP Laboratory, ENIT (France).  
Enables **simultaneous control** of a simulated and a physical Kinova Gen3 arm from a single MoveIt2 command.

---

## Background

This project integrates a **Clearpath Ridgeback** mobile platform and a **Kinova Gen3** robotic arm into a unified ROS2 environment.

A key challenge was that the simulated robot (Gazebo) and the physical robot use **different joint name conventions**:

| Robot | Joint name format |
|---|---|
| Gazebo simulation | `arm_0_joint_1` |
| Physical Kinova Gen3 | `joint_1` |

This mismatch prevents a single MoveIt2 trajectory from being sent to both robots directly.  
The **mirror node** solves this by subscribing to one topic and publishing to both robots with the appropriate joint name format.

---

## System Overview

```
MoveIt2 (RViz)
     ↓
/display_planned_path  (DisplayTrajectory)
     ↓
[ mirror_node ]
     ↓                        ↓
Gazebo simulated arm     Physical Kinova Gen3
(arm_0_joint_X)          (joint_X)
```

The node also accepts direct `JointTrajectory` commands via `/eps_arm/cmd` for terminal-based control.

---

## Demo

![EPS Mirror Node Demo](eps_demo.gif)

*MoveIt2 planned trajectory simultaneously executed on Gazebo simulation and physical Kinova Gen3.*

---

## Files

| File | Description |
|---|---|
| `eps_mirror_node.py` | Main node — subscribes to MoveIt2 and terminal commands, normalizes joint names, publishes to both robots |
| `display_to_eps_cmd.py` | Bridge node — converts `DisplayTrajectory` to `JointTrajectory` (integrated into mirror node v2) |
| `kinova_mirror_node.py` | Earlier version — mirror only, no MoveIt2 display topic support |
| `eps_sim.launch.py` | Launch file for full simulation (Gazebo + Nav2 + AMCL) |
| `eps_kinova.launch.py` | Launch file for physical Kinova bringup |
| `eps_kinova_connect.sh` | Bash script — automates network config and physical robot connection (lab-specific, edit before use) |
| `robot.yaml` | Clearpath robot configuration (Ridgeback + Kinova Gen3 + IMU) |

### Package Structure

These files belong to the following ROS2 workspace layout:

```
~/clearpath_ws/
└── src/
    ├── eps_bringup/        ← launch files (eps_sim.launch.py, eps_kinova.launch.py)
    ├── eps_mirror/         ← mirror node (eps_mirror_node.py, display_to_eps_cmd.py)
    ├── clearpath_*/        ← Clearpath Ridgeback packages
    ├── moveit2/            ← MoveIt2 motion planning
    └── ros2_kortex/        ← Kinova Gen3 driver
~/clearpath/
    ├── robot.yaml          ← robot configuration
    ├── warehouse.pgm       ← map file
    └── warehouse.yaml      ← map metadata
```

---

## Environment

- OS: Ubuntu 24.04
- ROS2: Jazzy Jalisco
- Simulation: Gazebo (Clearpath)
- Motion planning: MoveIt2
- Hardware: Kinova Gen3 7-DoF + Clearpath Ridgeback

---

## How to Run

### Simulation

```bash
ros2 launch eps_bringup eps_sim.launch.py
```

### Physical Robot

```bash
# Edit IFACE to match your network interface
chmod +x eps_kinova_connect.sh
./eps_kinova_connect.sh
```

### Mirror Node only

```bash
ros2 run eps_mirror mirror_node
```

---

## Development Notes

- Developed as part of **Team BOB**, EPS 2025, ENIT France
- Architecture, topic-flow design, integration, debugging, and validation by Hyojun Choi; initial code drafting assisted by AI
- Validated in Gazebo simulation before deployment on physical hardware
- ROS2 Rolling → **Jazzy** migration performed for better package compatibility (Clearpath stack)

### Design Evolution

The final node (`eps_mirror_node.py`) is the result of a two-stage development process:

**Stage 1 — Two separate nodes:**
- `kinova_mirror_node.py`: routes `JointTrajectory` commands to both simulation and physical robot, normalizing joint names for each
- `display_to_eps_cmd.py`: bridge node that converts MoveIt2's `DisplayTrajectory` output into executable `JointTrajectory` commands

**Stage 2 — Merged into one:**
- Both functionalities were combined into `eps_mirror_node.py` to simplify the command flow and reduce communication overhead
- The unified node handles both MoveIt2 planned trajectories and direct terminal commands through a single execution pipeline

---

## Future Work

- Reimplement in C++ for improved real-time performance
- Measure and quantify latency between simulation and physical robot
- Add safety checks (joint limit validation before publishing)
