# 트러블슈팅 & 엔지니어링 결정 기록

본 문서는 EPS Mobile Collaborative Robot 프로젝트의 sim-to-real 통합을 구축하는 과정에서 발생한 주요 문제들과, 필요할 때 팀 논의를 거쳐 해결한 과정을 기록합니다. 다음 EPS 학기 학생, 그리고 코드를 읽으며 *왜 이런 구조인지* 알고 싶은 분들을 위해 작성됐습니다.

**컨텍스트:** 저는 ROS 2 경험이 전혀 없는 상태에서 이 프로젝트에 참여했습니다. 아래의 아키텍처 결정들은 제가 직접 내린 것입니다. 코드 자체는 대부분 AI 보조로 초안을 작성한 뒤 제가 검토하고 테스트했으며, 우선 Gazebo에서, 그다음 실물 로봇에서 검증했습니다.

---

## 프로젝트 컨텍스트: Plan A에서 Plan B로

원래 Plan A는 완전한 물리 통합이었습니다: 실물 Ridgeback과 실물 Kinova Gen3를 단일 ROS 2 인터페이스로 제어하는 것.

학기 도중 실물 Ridgeback이 배터리 문제로 사용 불가능해졌고, 우리 일정 안에서는 해결할 수 없었습니다. 팀과 슈퍼바이저는 Plan B로 전환하기로 결정했습니다: 핵심 trajectory 라우팅 아키텍처는 그대로 유지하되, 시뮬레이션 Ridgeback과 실물 Kinova Gen3를 사용해 통합 시스템을 검증하는 방식입니다.

이 결정은 팀과 슈퍼바이저 레벨에서 내려진 것이며 제가 단독으로 결정한 일이 아닙니다. 그러나 이후 제 작업 범위에 영향을 미쳤습니다:

- Kinova sim-to-real mirroring 작업은 변경 없이 유지됐고 — 이것이 제 담당이자 핵심 기술 기여로 그대로 남았습니다.
- 실물 Ridgeback 제어와 base 위에서의 mobile manipulation은 이번 학기 범위에서 제외됐습니다.
- Gazebo 시뮬레이션이 Ridgeback 측의 표준(canonical) 환경이 됐고, 실물 Kinova는 동일한 trajectory 라우팅 로직이 실제 하드웨어를 구동할 수 있는지 검증하는 데 사용됐습니다.

README가 본 프로젝트를 완전한 물리 통합이 아닌 "시뮬레이션 Ridgeback + 실물 Kinova Gen3"로 기술하는 이유가 여기에 있습니다. 아래에서 다루는 mirror 노드, MoveIt 2 통합, launch 통합, 연결 워크플로우는 모두 Plan B 하에서 그대로 유효합니다.

---

## 1. Sim과 Real Kinova가 동일한 MoveIt 2 명령을 받아들이지 않음

**증상.** 실물 Kinova Gen3를 성공적으로 움직이게 한 MoveIt 2 trajectory가 Ridgeback에 마운트된 시뮬레이션 Kinova는 움직이지 못했고, 반대도 마찬가지였습니다.

**근본 원인.** 두 가지 불일치가 동시에 존재했습니다:

- **Joint 이름**
  - Sim: `arm_0_joint_1`, `arm_0_joint_2`, ...
  - Real: `joint_1`, `joint_2`, ...
- **Controller 토픽 namespace**
  - Sim: `/r100_0000/arm_0_joint_trajectory_controller/joint_trajectory`
  - Real: `/joint_trajectory_controller/joint_trajectory`

시뮬레이션 arm은 Ridgeback의 namespace(`/r100_0000/...`) 안에 위치합니다. 이는 Clearpath의 정상 동작 방식으로 — namespacing을 통해 여러 로봇이 Gazebo 내에서 토픽 충돌 없이 공존할 수 있게 합니다. 실물 Kinova에는 그런 namespace가 없습니다.

**Remap만으로는 부족했던 이유.** 처음에는 `ros2 topic remap`이나 launch 파일 파라미터 override로 해결하려 했습니다. 그러나 joint 이름은 토픽 이름이 아니라 `JointTrajectory` 메시지 **내부**에 들어있기 때문에 remap으로는 변경할 수 없었습니다. 메시지 자체를 다시 작성하는 노드가 필요했습니다.

**해결.** 다음을 수행하는 커스텀 mirror 노드:

1. 단일 trajectory 입력 구독.
2. `arm_0_` prefix를 추가해 sim controller로 발행.
3. `arm_0_` prefix를 제거해 real controller로 발행.
4. 위 두 동작을 동시 수행.

`eps_mirror_node.py` (MirrorNode v2)에 구현돼 있습니다.

---

## 2. Mirror 대상 MoveIt 2 토픽 선정

**문제.** MoveIt 2는 다양한 출력 채널을 노출합니다: `FollowJointTrajectory` action, planning scene, 내부 state 토픽, `/display_planned_path` 등. 어느 것을 source로 사용해야 할지 명확하지 않았습니다.

**선정 과정.** MoveIt 2 + Gazebo 전체 스택을 실행한 뒤 `rqt_graph`로 실시간 노드 그래프를 검사했습니다. RViz에서 **Plan**과 **Plan + Execute**를 눌렀을 때 계획된 motion이 어디에 나타나는지 추적했습니다. 다음 세 조건을 만족하는 토픽을 찾았습니다:

- 항상 **최종** trajectory를 담을 것 (중간 상태가 아닐 것).
- Plan **및** Plan+Execute 모드 모두에서 발행될 것.
- 그대로 재발행 가능한 형태로 데이터를 담을 것.

`/display_planned_path`가 위 세 조건을 모두 만족했습니다. MoveIt이 RViz에서 계획된 경로를 시각화하는 데 사용하는 토픽이며, 우리 셋업에서는 `JointTrajectory`로 변환해 양쪽 controller로 라우팅할 수 있는 실용적인 trajectory source 역할을 했습니다.

**결과.** MirrorNode v2는 `/display_planned_path`를 주 입력으로 구독하며, 터미널 테스트용으로 수동 `/eps_arm/cmd` 입력도 받습니다.

**크레딧.** "display 측" 토픽을 사용하자는 아이디어는 팀 논의 중 한 팀원에게서 나왔습니다. 저는 `rqt_graph`로 이를 검증한 뒤, 그 아이디어를 기반으로 bridge / mirror 구조를 구축했습니다.

---

## 3. `robot.yaml`이 Gazebo launch 시 크래시를 일으킴

**증상.** Clearpath `robot.yaml`을 수정해 Ridgeback 상단에 Kinova Gen3를 마운트하고 센서를 설정하던 중, Gazebo가 시작 시 크래시했습니다. 에러 메시지는 특정 라인을 명확히 지목하지 않았습니다.

**진단 방법.** YAML을 깨끗하게 실행되는 최소 구성(base만, manipulator 없음, 센서 없음)으로 축소한 뒤, 블록을 하나씩 다시 추가했습니다. 크래시가 발생할 때마다 직전에 추가한 블록이 원인이거나, 이미 존재하던 항목과 충돌하는 것이었습니다.

**결과.** 안정적인 최소 설정:

- `top_link`에 마운트된 Kinova Gen3 7-DOF arm,
- Microstrain IMU.

2D LiDAR 블록은 현재 주석 처리돼 있습니다 — 이슈 #6 참조.

---

## 4. ROS 2 Rolling이 우리 스택에서 불안정

**증상.** 프로젝트 브리프는 원래 ROS 2 Rolling을 명시했습니다. 초기 셋업 몇 주 동안 빌드가 반복적으로 깨졌고, 특히 Clearpath 패키지가 문제였습니다. Rolling은 LTS가 아니며 의존성이 사용자 코드 아래에서 계속 변하기 때문입니다.

**결정.** 전체 스택을 ROS 2 Jazzy (당시 LTS)로 마이그레이션할 것을 제안했습니다. MoveIt 2는 우리 환경에서 Rolling 위에서도 무리 없었지만, Clearpath 호환성이 주된 이유였습니다. 팀과 논의 후 모든 환경을 Jazzy로 이전했습니다.

**Trade-off.** Rolling 전용 기능 일부는 사용할 수 없게 됐지만, 4개월 일정을 고려하면 안정성이 더 중요했습니다.

---

## 5. 파편화된 launch 파일이 너무 많음

**증상.** 각 서브시스템(Gazebo, AMCL, Nav2, Kortex, mirror 노드, `cmd_vel` relay)이 각자의 launch 파일을 갖고 있었습니다. 전체 시스템을 시작하려면 터미널을 4~5개 열어야 했습니다.

**해결.** 모든 것을 두 개의 launch 파일로 통합:

- `eps_sim.launch.py` — 전체 시뮬레이션: Gazebo + AMCL + 정적 `map → odom` TF + Nav2 + `cmd_vel` relay.
- `eps_kinova.launch.py` — 실물 로봇: Kortex 드라이버 + MirrorNode v2.

또한 실물 로봇 launch 이전 호스트 측 네트워크 설정(방화벽 비활성화, 올바른 인터페이스에 static IP 할당, ping으로 연결 검증)을 처리하는 `eps_kinova_connect.sh`도 작성했습니다. 새 사용자들이 가장 자주 실수하던 부분입니다.

---

## 6. LiDAR 플러그인 추가 시 Gazebo 크래시 (미해결)

**증상.** `robot.yaml`에 Hokuyo 2D LiDAR 블록을 manipulator 블록과 동일한 스타일로 추가하자 Gazebo가 launch 시 segfault.

**시도한 것.**

- 다양한 sensor frame 파라미터,
- 다양한 마운팅 위치,
- URDF 생성 부분의 토글,
- `/scan`의 namespace prefix 재확인.

위 어떤 것도 안정적인 Gazebo launch를 만들어내지 못했습니다.

**상태.** 미해결. LiDAR 블록은 `robot.yaml`에서 주석 처리된 상태로 남겨뒀습니다. 이 문제가 해결되기 전까지는 시뮬레이션상 완전한 Nav2 자율주행에 제약이 있습니다.

**다음 팀을 위한 힌트.** 크래시는 config 포맷 에러가 아니라 플러그인 측 segfault로 보였습니다. 시도해볼 만한 것:

- 다른 Clearpath LiDAR 모델 항목,
- Gazebo classic 대신 Gz Sim (Ignition) sensor plugin 경로,
- 최소한의 standalone URDF 테스트로 플러그인을 나머지 스택에서 격리.

---

## 7. 통신 지연 (인정된 한계)

실물 로봇 테스트를 반복하던 중, 같은 trajectory를 실행할 때 시뮬레이션 arm과 실물 arm 사이에 미세한 timing 차이를 가끔 관찰했습니다.

**솔직히 밝히자면:** 학기 중에 적절한 도구로 이를 정량 측정하지는 못했습니다. 우선순위는 통합을 end-to-end로 동작시키는 것이었습니다. 지금 떠올릴 수 있는 가능한 원인들:

- Mirror 노드 안의 Python 인터프리터 오버헤드,
- Publisher 측 ROS 2 QoS / 큐 설정,
- Gazebo와 실물 로봇 스택을 함께 실행할 때의 호스트 시스템 부하.

이를 향후 과제로 남겨두고, 다음 iteration에서 정량 측정과 개선을 진행하기 위해 ROS 2 C++ 학습을 시작했습니다.

---

## 다음에 다르게 할 것

- 마지막 주가 아니라 첫날부터 end-to-end 지연시간 측정.
- Joint 이름 정규화 로직에 대한 단위 테스트 추가. 현재는 전체 스택 실행을 통해서만 테스트되고 있음.
- Mirror 노드에 안전 검사 추가 (예: 모델과 joint 개수가 일치하지 않는 trajectory 거부).
- 성능 향상 및 ROS 2 C++ API 학습 목적으로 mirror 노드를 C++로 재구현 시도.
