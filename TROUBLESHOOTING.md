# Troubleshooting & Engineering Decisions

This document records the main problems I ran into while building the sim-to-real integration for the EPS Mobile Collaborative Robot project, and how I worked through them with team discussion where needed. It is written for the next EPS cohort, and for anyone reading the code who wants to know *why* it looks the way it does.

**Context:** I came into this project with no prior ROS 2 experience. The architectural decisions below were mine. The code itself was mostly drafted with AI assistance, then reviewed and tested by me — first in Gazebo, then on the real robot.

---

## Project context: from Plan A to Plan B

The original Plan A was full physical integration: the real Ridgeback plus the real Kinova Gen3, controlled through a single ROS 2 interface.

Partway through the semester, the physical Ridgeback became unusable due to a battery issue that could not be resolved within our timeline. The team, together with the supervisors, decided to switch to Plan B: preserve the core trajectory-routing architecture, but validate the integrated system using a simulated Ridgeback plus the physical Kinova Gen3.

This decision was made at the team and supervisor level, not by me alone, but it shaped the rest of my work:

- The Kinova sim-to-real mirroring task stayed unchanged — this is what I was responsible for, and it remained the core technical contribution.
- Physical Ridgeback control and on-base mobile manipulation were dropped from this semester's scope.
- The Gazebo simulation became the canonical environment for the Ridgeback side, and the physical Kinova was used to validate that the same trajectory-routing logic could still drive real hardware.

This is the reason the README describes the project as "simulated Ridgeback + physical Kinova Gen3" rather than full physical integration. The mirror node, MoveIt 2 integration, launch consolidation, and connection workflow described below all remained valid under Plan B.

---

## 1. Sim and real Kinova did not accept the same MoveIt 2 command

**Symptom.** A MoveIt 2 trajectory that successfully moved the real Kinova Gen3 did not move the simulated Kinova mounted on the Ridgeback. The reverse was also true.

**Root cause.** There were two mismatches at the same time:

- **Joint names**
  - Sim: `arm_0_joint_1`, `arm_0_joint_2`, ...
  - Real: `joint_1`, `joint_2`, ...
- **Controller topic namespace**
  - Sim: `/r100_0000/arm_0_joint_trajectory_controller/joint_trajectory`
  - Real: `/joint_trajectory_controller/joint_trajectory`

The simulated arm sits inside the Ridgeback's namespace (`/r100_0000/...`). This is normal Clearpath behavior — namespacing lets multiple robots coexist in Gazebo without topic collisions. The real Kinova has no such namespace.

**Why a remap was not enough.** I first considered solving this with `ros2 topic remap` or with a launch-file parameter override. But the joint name lives **inside** the `JointTrajectory` message, not in the topic name, so a remap cannot rewrite it. We needed a node that rewrites the message itself.

**Fix.** A custom mirror node that:

1. Subscribes to a single trajectory input.
2. Adds the `arm_0_` prefix and publishes to the sim controller.
3. Removes the `arm_0_` prefix and publishes to the real controller.
4. Publishes both at the same time.

This is in `eps_mirror_node.py` (MirrorNode v2).

---

## 2. Choosing which MoveIt 2 topic to mirror from

**Problem.** MoveIt 2 exposes many output channels: a `FollowJointTrajectory` action, the planning scene, internal state topics, `/display_planned_path`, and more. It was not obvious which one to use as the source.

**How I picked it.** I launched the full MoveIt 2 + Gazebo stack and inspected the live node graph with `rqt_graph`. I traced where the planned motion appeared after pressing **Plan** and **Plan + Execute** in RViz. I looked for a topic that:

- Always carries the **final** trajectory (not an intermediate state),
- Is published in **both** Plan and Plan+Execute modes,
- Carries data in a form that can be republished directly.

`/display_planned_path` met all three. It is the topic MoveIt uses to visualize the planned path in RViz, and in our setup it provided a practical trajectory source that could be converted into a `JointTrajectory` and routed to both controllers.

**Result.** MirrorNode v2 subscribes to `/display_planned_path` as the main input, and also accepts a manual `/eps_arm/cmd` input for terminal testing.

**Credit.** The idea of using a "display-side" topic came from a teammate during a team discussion. I then validated it with `rqt_graph` and built the bridge / mirror around it.

---

## 3. `robot.yaml` made Gazebo crash on launch

**Symptom.** While modifying the Clearpath `robot.yaml` to mount the Kinova Gen3 on top of the Ridgeback and configure sensors, Gazebo crashed at startup. The error messages did not point clearly to a single line.

**How I diagnosed it.** I reduced the YAML to the minimum that launched cleanly (base only, no manipulator, no sensors), then re-added blocks one at a time. Each time it crashed, the last added block was the cause — or it conflicted with something already there.

**Result.** A stable minimal config with:

- The Kinova Gen3 7-DOF arm mounted on `top_link`,
- A Microstrain IMU.

The 2D LiDAR block is currently commented out — see Issue #6.

---

## 4. ROS 2 Rolling was unstable for our stack

**Symptom.** The project brief originally said ROS 2 Rolling. During the first weeks of setup, builds broke repeatedly — especially Clearpath packages — because Rolling is not LTS and its dependencies move underneath user code.

**Decision.** I proposed migrating the whole stack to ROS 2 Jazzy (the LTS at that time). MoveIt 2 was already fine on Rolling for us, but Clearpath compatibility was the main reason. After discussing it with the team, we migrated everything to Jazzy.

**Trade-off.** Some Rolling-only features were lost, but stability mattered more given the 4-month timeline.

---

## 5. Too many fragmented launch files

**Symptom.** Each subsystem (Gazebo, AMCL, Nav2, Kortex, mirror node, `cmd_vel` relay) had its own launch file. Starting the full system meant opening four or five terminals.

**Fix.** Consolidated everything into two launch files:

- `eps_sim.launch.py` — full simulation: Gazebo + AMCL + static `map → odom` TF + Nav2 + `cmd_vel` relay.
- `eps_kinova.launch.py` — real robot: Kortex driver + MirrorNode v2.

I also wrote `eps_kinova_connect.sh` to handle host-side network setup (disable firewall, assign static IP on the right interface, ping the robot to verify) before launching the real robot. This was the part new users got wrong most often.

---

## 6. Gazebo crashed when adding a LiDAR plugin (unresolved)

**Symptom.** Adding the Hokuyo 2D LiDAR block to `robot.yaml` — using the same style as the manipulator block — caused Gazebo to segfault at launch.

**What I tried.**

- Different sensor frame parameters,
- Different mounting positions,
- Toggling parts of the URDF generation,
- Re-checking namespace prefixes on `/scan`.

None of this gave a stable Gazebo launch.

**Status.** Unresolved. The LiDAR block is left commented out in `robot.yaml`. Full Nav2 autonomy in simulation is limited until this is fixed.

**Hint for the next team.** The crash looked like a plugin-side segfault rather than a config format error. It is probably worth trying:

- A different Clearpath LiDAR model entry,
- The Gz Sim (Ignition) sensor plugin path instead of the Gazebo classic one,
- A minimal standalone URDF test to isolate the plugin from the rest of the stack.

---

## 7. Communication latency (acknowledged limitation)

During repeated real-robot testing, I sometimes noticed small timing differences between the simulated arm and the real arm when executing the same trajectory.

**Honest disclosure:** I did not measure this with proper tooling during the semester. The focus was on making the integration work end to end. Possible causes I can think of now:

- Python interpreter overhead in the mirror node,
- ROS 2 QoS / queue settings on the publishers,
- Host system load when running Gazebo and the real-robot stack together.

I marked this as future work and have since started studying ROS 2 with C++ in order to measure and reduce this in a future iteration.

---

## What I would do differently next time

- Measure end-to-end latency from day 1, not as a final-week concern.
- Add unit tests for the joint-name normalization logic. Right now it is only tested by running the full stack.
- Add safety checks in the mirror node (e.g. reject trajectories whose joint count does not match the model).
- Try a C++ implementation of the mirror node, both for performance and to learn the ROS 2 C++ API properly.