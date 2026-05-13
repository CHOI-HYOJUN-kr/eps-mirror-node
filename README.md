# Mobile Collaborative Robot

EPS Fall 2025 — Team BOB
ENIT, Tarbes, France · Commissioned by LGP Lab (UTTOP)

A ROS 2 Jazzy stack for integrating a simulated Clearpath Ridgeback mobile base with a Kinova Gen3 7-DOF arm, and for validating the same MoveIt 2 trajectory on both the Gazebo-simulated Kinova and the physical Kinova Gen3.

![Demo](assets/eps_demo.gif)

> 한국어 버전 · [README_KR](./docs/README_KR.md) · [TROUBLESHOOTING_KR](./docs/TROUBLESHOOTING_KR.md)

## My Contribution (Hyojun Choi)

I was in charge of the Kinova Gen3 side of the integration, including the sim-to-real trajectory routing architecture, joint-name normalization, MoveIt 2 topic analysis with `rqt_graph`, launch-file consolidation, and the real-robot connection workflow.

This was my first robotics project, so I learned ROS 2 during the semester. I used AI tools to speed up code drafting, but the architecture, topic selection, message-flow validation, Gazebo-first testing, and real-robot verification were done by me.

What I did, concretely:

- **Found the sim ↔ real mismatch.** The simulated Kinova (on the Ridgeback) and the real Kinova used different joint name prefixes (`arm_0_joint_X` vs `joint_X`) **and** different controller namespaces (`/r100_0000/arm_0_joint_trajectory_controller/...` vs `/joint_trajectory_controller/...`). I brought this to the team and we agreed that a custom ROS 2 node was the cleanest way to solve both at once.

- **Chose the MoveIt 2 topic to mirror from.** MoveIt 2 publishes to many topics. I used `rqt_graph` to trace where the planned motion appears after pressing **Plan** and **Plan + Execute** in RViz, and used `/display_planned_path` as a practical trajectory source that could be converted into a `JointTrajectory` and routed to both controllers.

- **Designed the node and iterated three times:**
  - `kinova_mirror_node.py` — v1. Subscribes to `/eps_arm/cmd` and republishes to sim and real with the right prefix handling.
  - `display_to_eps_cmd.py` — bridge node added later, based on a teammate's idea, to convert MoveIt's `DisplayTrajectory` into a plain `JointTrajectory` on `/eps_arm/cmd`.
  - `eps_mirror_node.py` (MirrorNode v2) — merged the two into a single node that accepts either input and routes to sim and real at the same time.

- **Debugged the `robot.yaml` crash** by removing entries one by one until the launch stopped crashing, then rebuilt a minimal stable config.

- **Wrote the unified launch files** (`eps_sim.launch.py`, `eps_kinova.launch.py`) and the **network setup bash script** (`eps_kinova_connect.sh`) that prepares the host before connecting to the real robot.

- **Wrote the team's Setup Guide** so the next EPS cohort can reproduce the environment.

For the detailed problems I ran into and how I worked around them, see [**TROUBLESHOOTING.md**](./TROUBLESHOOTING.md).

## Node Architecture

```
MoveIt (RViz Plan / Plan+Execute)        Terminal command
            ↓                                   ↓
   /display_planned_path           /eps_arm/cmd (JointTrajectory)
            └───────────────┬───────────────────┘
                            ↓
                    [ MirrorNode v2 ]
                   (eps_mirror_node.py)
                       ↓           ↓
              Gazebo sim         Real Kinova Gen3
            (arm_0_joint_X)         (joint_X)
```

## Repository Layout

| Folder | Contents |
| --- | --- |
| `src/` | ROS 2 nodes: `eps_mirror_node.py` (MirrorNode v2), `display_to_eps_cmd.py` (bridge), `kinova_mirror_node.py` (v1) |
| `launch/` | `eps_sim.launch.py` (simulation), `eps_kinova.launch.py` (real robot) |
| `scripts/` | `eps_kinova_connect.sh` — automates host network config for the real Kinova |
| `config/` | `robot.yaml` (Clearpath robot description) |
| `assets/` | `rosgraph(final).png`, `TF tree.pdf`, `eps_demo.gif` |
| `docs/` | Team-level reports (Final Document, Setup Guide, summary) |

> Note: The `.launch.py` files are written assuming they live inside a ROS 2 package named `eps_bringup` in a Colcon workspace. To run the commands below, place them inside your own `eps_bringup` package. The Setup Guide in `docs/` explains the full workspace setup.

## Environment

- Ubuntu 24.04
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
```

The `eps_kinova_connect.sh` script configures the host network, verifies the robot connection, sources the ROS 2 workspace, and launches `eps_kinova.launch.py`.

## Project Period

2025-09-01 – 2025-12-18 · 30 ECTS · one semester

## License

MIT for the custom EPS code in this repository.
Third-party packages and documents follow their original licenses.
