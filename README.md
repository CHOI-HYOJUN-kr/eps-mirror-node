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

## Files

| File | Description |
|---|---|
| `eps_mirror_node.py` | Main node — subscribes to MoveIt2 and terminal commands, normalizes joint names, publishes to both robots |
| `display_to_eps_cmd.py` | Bridge node — converts `DisplayTrajectory` to `JointTrajectory` (integrated into mirror node v2) |
| `kinova_mirror_node.py` | Earlier version — mirror only, no MoveIt2 display topic support |
| `eps_sim_launch.py` | Launch file for full simulation (Gazebo + Nav2 + AMCL) |
| `eps_kinova_launch.py` | Launch file for physical Kinova bringup |
| `eps_kinova_connect.sh` | Bash script — automates network config and physical robot connection |
| `robot.yaml` | Clearpath robot configuration (Ridgeback + Kinova Gen3 + IMU) |

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
- Architecture designed by Hyojun Choi; code implemented with AI assistance
- Validated in Gazebo simulation before deployment on physical hardware
- ROS2 Rolling → **Jazzy** migration performed for better package compatibility (Clearpath stack)

---

## Future Work

- Reimplement in C++ for improved real-time performance
- Measure and quantify latency between simulation and physical robot
- Add safety checks (joint limit validation before publishing)
