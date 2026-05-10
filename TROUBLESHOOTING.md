# Troubleshooting Log

EPS Fall 2025 — Mobile Collaborative Robot (Team BOB)
LGP Research Lab, ENIT · UTTOP

A log of the concrete problems I (Hyojun Choi) ran into during the
project and how they were resolved. Each entry follows the same
structure: **Problem → Trial and error → Solution → Result**.

---

## Contents

1. [Choosing the ROS 2 distribution (Rolling → Jazzy)](#1-choosing-the-ros-2-distribution-rolling--jazzy)
2. [Joint name and controller namespace mismatch](#2-joint-name-and-controller-namespace-mismatch)
3. [Sending MoveIt output to both robots at once](#3-sending-moveit-output-to-both-robots-at-once)
4. [Merging the Mirror and Bridge nodes](#4-merging-the-mirror-and-bridge-nodes)
5. [Tracking down `robot.yaml` crashes](#5-tracking-down-robotyaml-crashes)
6. [Scattered launch steps → unified launcher and bash script](#6-scattered-launch-steps--unified-launcher-and-bash-script)
7. [Subtle timing differences between sim and real](#7-subtle-timing-differences-between-sim-and-real)

---

## 1. Choosing the ROS 2 distribution (Rolling → Jazzy)

**Problem.** The initial requirement was to build on ROS 2 Rolling, but
Rolling is a continuously updated rolling release and package
compatibility shifted frequently. The Clearpath simulation packages in
particular kept hitting dependency conflicts that were hard to pin
down.

**Trial and error.** I first tried to stay on Rolling and pin individual
package versions. Stabilizing one package would break another, and the
problem just moved around. MoveIt itself was fine on Rolling; the
damage accumulated on the Clearpath side.

**Solution.** I proposed switching the project to ROS 2 Jazzy (the LTS
line), prepared a short compatibility check, and reached agreement
with the team. After the switch, the random build failures dropped
sharply.

**Result.** Over the following two months of development, environment
itself was almost never the cause of build failures. Debugging time
could be spent on the actual code and integration issues instead.

---

## 2. Joint name and controller namespace mismatch

**Problem.** The same Kinova Gen3 was being addressed differently in
simulation and on the real robot:

- Real: `joint_1`, `joint_2`, … on `/joint_trajectory_controller/...`
- Sim:  `arm_0_joint_1`, … on `/r100_0000/arm_0_joint_trajectory_controller/...`

The `arm_0_` prefix and namespace exist so that Gazebo can host
multiple robots at once, but as a result the same `JointTrajectory`
message would be accepted by one side and silently ignored by the
other.

**Trial and error.** I first tried two separate publishing scripts, one
per robot. That meant the same motion had to be published twice and
introduced small timing offsets between sim and real. I also tried
forcing a `remap` from the MoveIt launch arguments, which led to
controller spec conflicts in `ros2_control`.

**Solution.** In a team discussion I proposed a "single input topic +
small routing node" design and we agreed on it. A unified topic
`/eps_arm/cmd` became the only place a publisher needs to write to;
`MirrorNode` consumes it and re-publishes to both controllers,
adding the `arm_0_` prefix for the simulated arm and stripping it for
the real one. The node was written against the official ROS 2
documentation and message definitions, drafted, and refined through
repeated tests.

**Result.** Any upstream module — test scripts, MoveIt integration —
only had to publish once to a single topic, and both robots received
the command synchronously. Every later piece of work could rely on
this one interface.

---

## 3. Sending MoveIt output to both robots at once

**Problem.** The routing structure above worked well for script-driven
commands, but MoveIt's *Plan + Execute* button in RViz did not publish
to `/eps_arm/cmd`. MoveIt sends execution commands directly to a
controller topic that is bound to one side only.

**Trial and error.** I tried mapping MoveIt's `controller.yaml` to both
controllers at once, but the controller manager refuses to bind two
controllers to the same joint set. The first thing I actually needed
was a clearer picture of which topics MoveIt publishes and which of
them are usable as a tap point.

**Solution.** I traced MoveIt's pub/sub graph with `rqt_graph`, and
adopted a teammate's idea of using `/display_planned_path`
(`DisplayTrajectory`) — the topic MoveIt uses to draw trajectories in
RViz. I wrote a `DisplayToEpsCmd` node that subscribes to it,
extracts the `JointTrajectory` from the first `RobotTrajectory`,
normalizes joint names, and re-publishes it as a plain
`JointTrajectory` on `/eps_arm/cmd`.

**Result.** Pressing *Plan + Execute* in RViz alone made both the
simulated and the real Kinova execute the same path simultaneously.
For demos there was no longer any extra command flow on top of MoveIt.

---

## 4. Merging the Mirror and Bridge nodes

**Problem.** The two steps above left two nodes running at the same
time: `MirrorNode` (sim ↔ real routing) and the `DisplayToEpsCmd`
"bridge" (MoveIt → unified cmd). Each message took an extra hop,
and the more nodes there were, the harder launch, debugging, and log
tracing became.

**Trial and error.** I first considered keeping them separate and just
grouping them in one launch file. That cleaned up the bring-up but
not the runtime path: a message still had to go
`/display_planned_path → /eps_arm/cmd → both controllers`.

**Solution.** I redefined the responsibility split. *MoveIt input* and
*manual command input* both end with the same normalize-and-publish
logic, so I merged them into a single node (`MirrorNode v2`) that
accepts both inputs and calls one `normalize_and_publish()` function.
Two input channels (`/display_planned_path`, `/eps_arm/cmd`), two
output channels (sim controller, real controller).

**Result.** The node graph collapsed by one stage and the launch file
had one fewer process to start. I did not measure latency, but in the
pre-demo environment the response to *Plan + Execute* felt more
consistent. More importantly, when something went wrong there was
only one node to suspect.

---

## 5. Tracking down `robot.yaml` crashes

**Problem.** The Clearpath simulation declares the base, sensors, and
attachments through `robot.yaml`. While adding the Kinova Gen3, IMU,
and other parts, the build itself would pass but the simulation would
fail at startup — missing TF frames, controllers failing to spawn, or
the simulator crashing — and the failure was not deterministic.

**Trial and error.** Writing the entire configuration in one go and
seeing whether it ran did not point at the cause. The logs were
inconsistent, which made the failure hard to even reproduce.

**Solution.** I shrank the configuration to the bare minimum and added
parts back one at a time — a binary-search style debugging pass.

1. Base platform only → check TF tree with `tf2_echo`, check controller
   manager status
2. Add IMU → re-verify
3. Add arm mount → verify
4. Add Kinova Gen3 → verify
5. Add gripper → verify

When something broke, the only thing that had changed was that
step's YAML block, so the cause was unambiguous.

**Result.** The `robot.yaml` produced this way held up for the rest of
the project, and other teammates were able to reproduce the
environment from the same file.

---

## 6. Scattered launch steps → unified launcher and bash script

**Problem.** Right before a real-robot demo, bringing up the stack
required opening four to five terminals in a fixed order: setting the
robot's IP, checking the connection, starting MoveIt, starting
`MirrorNode`, etc. Just before the presentation, this was the single
biggest source of risk.

**Trial and error.** I tried collapsing the steps with shell aliases.
That shortened the typing, but if any step failed it was not obvious
where to resume.

**Solution.**

- Simulation side: `eps_sim.launch.py` brings up Gazebo, AMCL, the
  static `map → odom` TF, Nav2, and the `cmd_vel` relay in one file.
- Real-robot side: `eps_kinova.launch.py` declares both the Kortex
  driver and the `MirrorNode v2` parameters together.
- Connection: `eps_kinova_connect.sh` consolidates IP setup and
  health checks into a single script.

**Result.** The bring-up procedure shrank to *one bash script + two
`ros2 launch` commands*. The chance of breaking the demo with a typo
went down sharply, and the next semester's students have a much
lower barrier to reproducing the same stack.

---

## 7. Subtle timing differences between sim and real

**Problem.** When running both robots together in repeated tests, I
occasionally observed small differences between them — not large
enough to count as failures or collisions, but a slight delay or
profile difference for the same command.

**Trial and error.** Within the project schedule I could not afford a
quantitative root-cause analysis. There were too many candidates —
message queue handling, QoS settings, lack of real-time guarantees,
host load, internal interpolation on the real controller — to pin
down in the time available.

**Solution (within the scope of this semester).** I focused on the
parts that could affect the demo. I kept the command publishing rate
steady, kept the routing structure that delivers the same message to
both sides simultaneously, and fixed the validation procedure to run
in Gazebo first and only then move to the real robot.

**Limitation acknowledged.** I did not produce a quantitative analysis
of whether the cause was message handling, runtime load, or something
else.

**Follow-up.** Since coming back, I have been studying ROS 2 with C++
to see how the same kind of synchronization and execution issues are
handled in a different language and runtime stack.

---

## Retrospective

The biggest takeaway was the habit of *splitting problems into smaller
pieces*. Writing the entire `robot.yaml` at once and looking only at
the result almost always hid the cause; reassembling it part by part
and verifying each step was much faster in practice. The same applied
to the node structure: what made the eventual merge of Mirror and
Bridge clean was not the merge itself but the fact that, *before*
merging, both inputs had already been routed through the same
function.

The other one was the leverage of *a single shared interface*. Once
`/eps_arm/cmd` was fixed as the unified topic, every later piece of
work — MoveIt integration, node consolidation, launch cleanup —
naturally aligned around it.
