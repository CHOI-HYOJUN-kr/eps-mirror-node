# 트러블슈팅 & 엔지니어링 결정 기록

이 문서는 EPS Mobile Collaborative Robot 프로젝트에서 sim-to-real 통합을 구축하는 과정에서 겪은 주요 문제들과, 필요한 경우 팀 논의를 거쳐 이를 해결한 과정을 기록한 문서입니다. 다음 EPS 기수 학생들과, 코드를 읽으며 *왜 이런 구조로 되어 있는지* 알고 싶은 사람을 위해 작성했습니다.

**Context:** 저는 ROS 2 경험이 전혀 없는 상태에서 이 프로젝트에 참여했습니다. 아래에 정리한 구조 관련 결정은 제가 직접 내린 것입니다. 코드 자체는 대부분 AI의 도움을 받아 초안을 작성했고, 이후 제가 검토하고 테스트했습니다. 테스트는 먼저 Gazebo에서 수행한 뒤, 실물 로봇으로 옮겨 진행했습니다.

---

## 프로젝트 컨텍스트: Plan A에서 Plan B로

원래 Plan A는 완전한 물리 통합이었습니다. 즉, 실물 Ridgeback과 실물 Kinova Gen3를 하나의 ROS 2 인터페이스로 제어하는 것이 목표였습니다.

그러나 학기 중반에 실물 Ridgeback이 배터리 문제로 사용 불가능해졌고, 프로젝트 일정 안에서는 이를 해결할 수 없었습니다. 이에 따라 팀과 supervisor는 Plan B로 전환하기로 결정했습니다. Plan B는 핵심 trajectory 전달 구조는 유지하되, 시뮬레이션 Ridgeback과 실물 Kinova Gen3를 사용해 통합 시스템을 검증하는 방식이었습니다.

이 결정은 제가 단독으로 내린 것이 아니라 팀과 supervisor가 함께 내린 결정이었습니다. 다만 이후 제 작업 범위에는 직접적인 영향을 주었습니다.

- Kinova sim-to-real mirroring 작업은 그대로 유지되었습니다. 이 부분이 제 담당이었고, 프로젝트의 핵심 기술 기여로 남았습니다.
- 실물 Ridgeback 제어와 base 위에서의 mobile manipulation은 이번 학기 범위에서 제외되었습니다.
- Gazebo simulation은 Ridgeback 측 검증의 기준 환경이 되었고, 실물 Kinova는 동일한 trajectory 전달 로직이 실제 하드웨어도 구동할 수 있는지 검증하는 데 사용되었습니다.

README에서 이 프로젝트를 완전한 물리 통합이 아니라 "시뮬레이션 Ridgeback + 실물 Kinova Gen3"로 설명하는 이유가 여기에 있습니다. 아래에서 설명하는 mirror node, MoveIt 2 통합, launch 통합, connection workflow는 모두 Plan B 범위에서도 유효했습니다.

---

## 1. 시뮬레이션 Kinova와 실물 Kinova가 동일한 MoveIt 2 명령을 받아들이지 않음

**증상.** 실물 Kinova Gen3를 성공적으로 움직이던 MoveIt 2 trajectory가 Ridgeback에 마운트된 시뮬레이션 Kinova는 움직이지 못했습니다. 반대의 경우도 마찬가지였습니다.

**근본 원인.** 두 가지 mismatch가 동시에 존재했습니다.

- **Joint names**
  - Sim: `arm_0_joint_1`, `arm_0_joint_2`, ...
  - Real: `joint_1`, `joint_2`, ...

- **Controller topic namespace**
  - Sim: `/r100_0000/arm_0_joint_trajectory_controller/joint_trajectory`
  - Real: `/joint_trajectory_controller/joint_trajectory`

시뮬레이션 arm은 Ridgeback의 namespace인 `/r100_0000/...` 안에 위치합니다. 이는 Clearpath의 일반적인 동작 방식입니다. Gazebo 안에서 여러 robot이 동시에 존재할 때, namespacing은 topic collision을 방지합니다. 반면 실물 Kinova에는 이러한 namespace가 없습니다.

**Remap만으로는 부족했던 이유.** 처음에는 `ros2 topic remap`이나 launch file parameter override로 해결할 수 있을지 검토했습니다. 하지만 joint name은 topic name이 아니라 `JointTrajectory` message 내부에 들어 있습니다. 따라서 remap만으로는 이를 수정할 수 없었습니다. message 자체를 다시 작성하는 node가 필요했습니다.

**해결.** 다음 기능을 수행하는 custom mirror node를 만들었습니다.

1. 하나의 trajectory input을 subscribe합니다.
2. `arm_0_` prefix를 추가해 sim controller로 publish합니다.
3. `arm_0_` prefix를 제거해 real controller로 publish합니다.
4. 두 controller로 동시에 publish합니다.

이 기능은 `eps_mirror_node.py` (MirrorNode v2)에 구현되어 있습니다.

---

## 2. Mirror 대상으로 사용할 MoveIt 2 topic 선정

**문제.** MoveIt 2는 여러 output channel을 제공합니다. 예를 들어 `FollowJointTrajectory` action, planning scene, internal state topics, `/display_planned_path` 등이 있습니다. 처음에는 이 중 어떤 것을 source로 사용해야 할지 명확하지 않았습니다.

**선정 과정.** MoveIt 2 + Gazebo 전체 stack을 실행한 뒤, `rqt_graph`로 live node graph를 확인했습니다. RViz에서 **Plan**과 **Plan + Execute**를 눌렀을 때 planned motion이 어디에 나타나는지 추적했습니다. 저는 다음 조건을 만족하는 topic을 찾았습니다.

- 항상 **최종 trajectory**를 담고 있을 것. 즉, intermediate state가 아닐 것.
- **Plan**과 **Plan+Execute** mode 모두에서 publish될 것.
- 다시 publish할 수 있는 형태의 data를 담고 있을 것.

`/display_planned_path`가 위 세 조건을 모두 만족했습니다. 이 topic은 MoveIt이 RViz에서 planned path를 visualize할 때 사용하는 topic이며, 저희 setup에서는 `JointTrajectory`로 변환해 양쪽 controller로 전달할 수 있는 practical trajectory source로 사용할 수 있었습니다.

**결과.** MirrorNode v2는 `/display_planned_path`를 main input으로 subscribe합니다. 또한 terminal test를 위해 manual input인 `/eps_arm/cmd`도 받을 수 있습니다.

**Credit.** "display-side" topic을 사용하자는 아이디어는 팀 논의 중 한 팀원에게서 나왔습니다. 저는 이 아이디어를 `rqt_graph`로 검증했고, 이를 바탕으로 bridge / mirror 구조를 구축했습니다.

---

## 3. `robot.yaml` 때문에 Gazebo가 launch 중 crash함

**증상.** Clearpath `robot.yaml`을 수정해 Ridgeback 상단에 Kinova Gen3를 mount하고 sensor를 설정하는 과정에서 Gazebo가 startup 중 crash했습니다. Error message는 문제가 되는 특정 line을 명확하게 가리키지 않았습니다.

**진단 방법.** YAML을 정상적으로 launch되는 최소 구성으로 줄였습니다. 즉, base만 남기고 manipulator와 sensor는 모두 제외한 상태에서 시작했습니다. 이후 block을 하나씩 다시 추가했습니다. crash가 발생하면, 마지막으로 추가한 block이 원인이거나 기존 항목과 conflict를 일으킨 것이라고 판단할 수 있었습니다.

**결과.** 다음을 포함하는 안정적인 최소 설정을 만들었습니다.

- `top_link`에 mount된 Kinova Gen3 7-DOF arm
- Microstrain IMU

2D LiDAR block은 현재 comment out되어 있습니다. 자세한 내용은 Issue #6을 참고하면 됩니다.

---

## 4. ROS 2 Rolling이 우리 stack에서 불안정했음

**증상.** Project brief에서는 원래 ROS 2 Rolling을 사용하라고 되어 있었습니다. 하지만 setup 초기 몇 주 동안 build가 반복적으로 깨졌고, 특히 Clearpath package에서 문제가 많이 발생했습니다. Rolling은 LTS가 아니어서 의존성 버전이 계속 바뀌고, 그 영향으로 기존 코드가 갑자기 깨질 수 있었습니다.

**결정.** 저는 전체 stack을 ROS 2 Jazzy로 migration하자고 제안했습니다. 저희 환경에서는 MoveIt 2 자체는 Rolling에서도 문제없이 동작했지만, Clearpath compatibility가 핵심 문제였습니다. 팀과 논의한 뒤 전체 환경을 Jazzy로 이전했습니다.

**Trade-off.** 일부 Rolling-only feature는 사용할 수 없게 되었지만, 4개월이라는 제한된 일정에서는 stability가 더 중요했습니다.

---

## 5. Launch file이 너무 많이 분산되어 있었음

**증상.** 각 subsystem(Gazebo, AMCL, Nav2, Kortex, mirror node, `cmd_vel` relay)마다 별도의 launch file이 존재했습니다. 전체 system을 시작하려면 terminal을 4~5개 열어야 했습니다.

**해결.** 모든 것을 두 개의 launch file로 통합했습니다.

- `eps_sim.launch.py` — full simulation: Gazebo + AMCL + static `map → odom` TF + Nav2 + `cmd_vel` relay
- `eps_kinova.launch.py` — real robot: Kortex driver + MirrorNode v2

또한 실물 로봇 launch 전에 PC 네트워크 설정을 처리하기 위해 `eps_kinova_connect.sh`를 작성했습니다. 이 script는 firewall을 disable하고, 올바른 network interface에 static IP를 할당하며, robot에 ping을 보내 connection을 확인합니다. 새 사용자가 가장 자주 실수하던 부분이 바로 이 단계였습니다.

---

## 6. LiDAR plugin 추가 시 Gazebo crash — unresolved

**증상.** Hokuyo 2D LiDAR block을 `robot.yaml`에 추가하자, manipulator block과 같은 style로 작성했음에도 Gazebo가 launch 중 segmentation fault를 일으켰습니다.

**시도한 것.**

- 여러 sensor frame parameter
- 여러 mounting position
- URDF generation 일부 설정 변경
- `/scan`의 namespace prefix 재확인

하지만 어떤 시도도 안정적인 Gazebo launch로 이어지지는 않았습니다.

**상태.** unresolved 상태입니다. LiDAR block은 `robot.yaml`에서 comment out된 상태로 남겨두었습니다. 이 문제가 해결되기 전까지는 Nav2 기반의 완전한 자율주행 검증에는 제약이 있습니다.

**다음 팀을 위한 힌트.** 이 crash는 config format error라기보다는 plugin-side segfault처럼 보였습니다. 다음 항목을 시도해볼 만합니다.

- 다른 Clearpath LiDAR model entry 사용
- Gazebo classic 대신 Gz Sim (Ignition) sensor plugin path 사용
- 최소한의 standalone URDF test로 plugin을 나머지 stack과 분리해 확인

---

## 7. 통신 지연 — 인정한 한계

반복적인 real-robot testing 중, 같은 trajectory를 실행할 때 simulated arm과 real arm 사이에 작은 timing difference가 보이는 경우가 있었습니다.

**솔직히 밝히자면:** 학기 중에는 이를 적절한 도구로 정량 측정하지 못했습니다. 당시 우선순위는 end-to-end integration을 완성하는 것이었습니다. 지금 생각해볼 수 있는 가능한 원인은 다음과 같습니다.

- Mirror node의 Python interpreter overhead
- Publisher 측 ROS 2 QoS / queue settings
- Gazebo와 real-robot stack을 함께 실행할 때의 host system load

이 부분은 future work로 남겼고, 이후 다음 개선 단계에서 정량 측정과 개선을 진행하기 위해 ROS 2 with C++를 공부하기 시작했습니다.

---

## 다음에 다르게 할 것

- End-to-end latency를 마지막 주의 문제가 아니라 프로젝트 초반부터 측정할 것입니다.
- Joint-name normalization logic에 대한 unit test를 추가할 것입니다. 현재는 full stack을 실행하는 방식으로만 테스트되어 있습니다.
- Mirror node에 safety check를 추가할 것입니다. 예를 들어 trajectory의 joint count가 model과 맞지 않으면 reject하도록 할 수 있습니다.
- 성능 개선과 ROS 2 C++ API 학습을 위해 mirror node의 C++ implementation을 시도할 것입니다.
