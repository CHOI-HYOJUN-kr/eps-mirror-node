# Mobile Collaborative Robot

EPS Fall 2025 — Team BOB
ENIT, Tarbes, France · LGP Lab (UTTOP) 의뢰 프로젝트

Clearpath Ridgeback 모바일 베이스와 Kinova Gen3 7-DOF 매니퓰레이터를 시뮬레이션 환경에서 통합한 프로젝트입니다. ROS 2 Jazzy를 사용했으며, 동일한 MoveIt 2 궤적을 Gazebo의 Kinova 모델과 실물 Kinova Gen3 양쪽에서 검증할 수 있도록 구성했습니다.

![Demo](../assets/eps_demo.gif)

> English version · [README](../README.md) · [TROUBLESHOOTING](../TROUBLESHOOTING.md)

## 담당 작업 — 최효준

프로젝트에서 **Kinova Gen3 통합**을 담당했습니다. 시뮬레이션 로봇과 실물 로봇에 궤적을 전달하는 방식을 설계하고, 관절명과 controller namespace의 차이를 정리했습니다. MoveIt 2에서 생성한 궤적이 양쪽 로봇으로 전달되는지도 검증했습니다.

ROS 2 경험 없이 시작한 첫 로봇 프로젝트로, 학기 중 ROS 2를 처음부터 배우며 진행했습니다. 코드 초안을 빠르게 작성하는 데 AI 도구를 활용했습니다. 구조 설계와 토픽 선정, 메시지 전달 검증은 직접 했습니다. 테스트도 Gazebo에서 먼저 진행하고, 이후 실물 Kinova에서 검증했습니다.

구체적인 작업은 다음과 같습니다.

* **Simulation ↔ Real 환경의 차이를 파악했습니다.**
  Ridgeback에 장착된 시뮬레이션 Kinova와 실물 Kinova Gen3는 관절명 접두어와 controller namespace가 서로 달랐습니다.

  * Simulation: `arm_0_joint_X`
  * Real Kinova: `joint_X`
  * Simulation controller: `/r100_0000/arm_0_joint_trajectory_controller/...`
  * Real controller: `/joint_trajectory_controller/...`

  이 차이 때문에 MoveIt 2에서 생성한 궤적을 그대로 양쪽 로봇에 동시에 전달하기 어려웠습니다. 팀에 문제를 공유한 뒤, 관절명 정규화와 토픽 remapping을 처리하는 별도의 ROS 2 노드를 두는 것이 가장 적절하다고 판단했습니다. 팀과도 이 방식으로 합의했습니다.

* **MoveIt 2에서 궤적을 받아올 토픽을 선정했습니다.**
  MoveIt 2는 계획과 실행 과정에서 여러 토픽으로 메시지를 발행합니다. RViz에서 **Plan**과 **Plan + Execute**를 실행했을 때 계획한 동작이 어느 토픽에 나타나는지 `rqt_graph`로 추적했습니다. 그 결과 `/display_planned_path`를 궤적 입력으로 선택했습니다. 이 토픽의 메시지를 `JointTrajectory`로 변환해 controller에 전달하도록 구현했습니다.

* **Trajectory mirror node를 설계하고 단계적으로 개선했습니다.**

  * `kinova_mirror_node.py`
    초기 버전입니다. `/eps_arm/cmd`를 구독해 관절명 접두어를 처리한 뒤, simulation controller와 real Kinova controller 양쪽으로 궤적을 다시 발행합니다.

  * `display_to_eps_cmd.py`
    팀원의 아이디어를 바탕으로 추가한 bridge node입니다. MoveIt 2의 `DisplayTrajectory` 메시지를 일반 `JointTrajectory`로 변환해 `/eps_arm/cmd`로 전달합니다.

  * `eps_mirror_node.py`
    두 기능을 하나의 노드로 통합한 최종 버전 MirrorNode v2입니다. MoveIt 2에서 생성한 궤적과 터미널에서 직접 입력한 궤적을 모두 받아 simulation Kinova와 real Kinova controller로 동시에 전달합니다.

* **`robot.yaml` 설정으로 인한 launch crash를 디버깅했습니다.**
  launch 과정에서 crash가 발생해 `robot.yaml` 항목을 하나씩 제거하며 원인을 좁혔습니다. 이후 안정적으로 동작하는 데 필요한 최소 설정을 다시 구성했습니다.

* **시뮬레이션과 실물 로봇 실행용 launch 파일을 작성했습니다.**

  * `eps_sim.launch.py` — Gazebo 시뮬레이션 실행용 launch 파일
  * `eps_kinova.launch.py` — 실물 Kinova Gen3 연결·실행용 launch 파일

* **실물 Kinova 연결용 bash 스크립트를 작성했습니다.**
  `eps_kinova_connect.sh`로 PC 네트워크 설정부터 로봇 연결 확인, ROS 2 workspace 환경 불러오기, real Kinova launch 실행까지 자동화했습니다.

* **팀 Setup Guide를 작성했습니다.**
  다음 EPS 기수 학생들이 같은 환경을 재현할 수 있도록 시뮬레이션 실행, 실물 Kinova 연결, troubleshooting 절차를 문서로 정리했습니다.

프로젝트 중 겪은 주요 문제와 해결 과정은 [**TROUBLESHOOTING_KR.md**](./TROUBLESHOOTING_KR.md)에 정리했습니다.

## 노드 아키텍처

```text
MoveIt 2 (RViz Plan / Plan + Execute)      Terminal command
                  ↓                              ↓
        /display_planned_path          /eps_arm/cmd (JointTrajectory)
                  └──────────────┬───────────────┘
                                 ↓
                         [ MirrorNode v2 ]
                        (eps_mirror_node.py)
                            ↓          ↓
                    Gazebo Kinova   Real Kinova Gen3
                   (arm_0_joint_X)      (joint_X)
```

## 저장소 구조

| 폴더         | 내용                                                                                                                |
| ---------- | ----------------------------------------------------------------------------------------------------------------- |
| `src/`     | ROS 2 nodes: `eps_mirror_node.py` (MirrorNode v2), `display_to_eps_cmd.py` (bridge), `kinova_mirror_node.py` (v1) |
| `launch/`  | `eps_sim.launch.py` (simulation), `eps_kinova.launch.py` (real robot)                                             |
| `scripts/` | `eps_kinova_connect.sh` — 실물 Kinova 연결용 PC 네트워크 설정 및 launch 자동화                                                   |
| `config/`  | `robot.yaml` — Clearpath robot description 설정                                                                     |
| `assets/`  | `rosgraph(final).png`, `TF tree.pdf`, `eps_demo.gif`                                                              |
| `docs/`    | 한국어 문서: README, TROUBLESHOOTING, 프로젝트 요약본                                                                         |

> 참고: `.launch.py` 파일은 Colcon workspace의 `eps_bringup` ROS 2 package 안에 두고 사용하도록 작성했습니다. 아래 명령을 실행하려면 해당 파일을 본인의 `eps_bringup` package 안에 배치해야 합니다.

## 환경

* Ubuntu 24.04
* ROS 2 Jazzy
* Gazebo
* Clearpath simulation packages
* MoveIt 2
* Kinova Kortex ROS 2 driver

## 실행

```bash
# Simulation
ros2 launch eps_bringup eps_sim.launch.py

# Real Kinova
IFACE=enp3s0 bash scripts/eps_kinova_connect.sh
```

`eps_kinova_connect.sh`는 PC 네트워크를 설정하고 로봇 연결을 확인한 뒤, ROS 2 workspace 환경을 불러와 `eps_kinova.launch.py`를 실행합니다.

## 프로젝트 기간

2025-09-01 – 2025-12-18 · 30 ECTS · 한 학기 프로젝트

## License

이 저장소의 EPS custom code에는 MIT License를 적용합니다.
외부 package와 문서는 각각의 원본 license를 따릅니다.
