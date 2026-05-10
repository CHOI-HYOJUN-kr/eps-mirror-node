# Mobile Collaborative Robot

EPS Fall 2025 — Team BOB
LGP Research Lab (ENIT · UTTOP), France

A ROS 2 Jazzy stack that integrates a Clearpath Ridgeback mobile base
and a Kinova Gen3 7-DOF arm, so that the same MoveIt 2 trajectory runs
on both the Gazebo simulation and the real robot at the same time.

## My Contribution (Hyojun Choi)

Responsible for the Kinova Gen3 side. Proposed and implemented the
structure of `MirrorNode v2`, which routes trajectories between the
simulated and real arms, and put together the unified launch files,
the connection script, the `robot.yaml` stabilization work, and the
Gazebo-to-real trajectory equivalence check. Also contributed to the
writing and organization of the Setup Guide. The full reasoning,
trade-offs, and step-by-step problem solving are documented in
[**TROUBLESHOOTING.md**](./TROUBLESHOOTING.md).

## Repository Layout

| Folder | Contents |
| --- | --- |
| `src/` | ROS 2 nodes (`eps_mirror_node.py`, `display_to_eps_cmd.py`, …) |
| `launch/` | Simulation and real-robot bring-up launch files |
| `scripts/` | Bash helper for connecting to the real Kinova |
| `config/` | `robot.yaml` (Clearpath robot description) |
| `assets/` | Graphs, TF tree, demo recordings |
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
