# Mobile Collaborative Robot

EPS Fall 2025 — Team BOB
ENIT, Tarbes, France · LGP Lab (UTTOP) 의뢰 프로젝트

Clearpath Ridgeback 모바일 베이스와 Kinova Gen3 7-DOF 매니퓰레이터를 시뮬레이션 환경에서 통합하고, 동일한 MoveIt 2 trajectory를 Gazebo 시뮬레이션 Kinova와 실물 Kinova Gen3 양쪽에서 검증하기 위해 구축한 ROS 2 Jazzy 기반 스택이다.

![Demo](../assets/eps_demo.gif)

> English version · [README](../README.md) · [TROUBLESHOOTING](../TROUBLESHOOTING.md)

## 담당 기여 — 최효준

저는 프로젝트에서 **Kinova Gen3 통합 파트**를 담당했다. 주요 역할은 시뮬레이션 로봇과 실물 로봇 사이의 trajectory 전달 구조를 설계하고, joint name 차이와 controller namespace 차이를 정리하며, MoveIt 2에서 생성된 trajectory가 양쪽 로봇으로 전달되는 흐름을 검증하는 것이었다.

이 프로젝트는 제가 처음 수행한 로봇 프로젝트였다. 학기 중 ROS 2를 처음부터 학습하며 진행했고, 코드 초안 작성 속도를 높이기 위해 AI 도구도 활용했다. 다만 전체 구조 설계, topic 선정, message flow 검증, Gazebo 우선 테스트, 실물 Kinova 검증은 직접 수행했다.

구체적으로 수행한 작업은 다음과 같다.

* **Simulation ↔ Real 환경의 불일치 문제를 파악했다.**
  Ridgeback에 마운트된 시뮬레이션 Kinova와 실물 Kinova Gen3는 서로 다른 joint name prefix와 controller namespace를 사용하고 있었다.

  * Simulation: `arm_0_joint_X`
  * Real Kinova: `joint_X`
  * Simulation controller: `/r100_0000/arm_0_joint_trajectory_controller/...`
  * Real controller: `/joint_trajectory_controller/...`

  이 차이로 인해 MoveIt 2에서 생성한 trajectory를 그대로 양쪽 로봇에 동시에 전달하기 어려웠다. 저는 이 문제를 팀에 공유했고, joint name 정규화와 topic remapping을 담당하는 별도의 ROS 2 node를 두는 방식이 가장 적절하다고 판단해 팀과 구조를 합의했다.

* **MoveIt 2 trajectory source로 사용할 topic을 선정했다.**
  MoveIt 2는 planning 및 execution 과정에서 여러 topic을 발행한다. 저는 RViz에서 **Plan**과 **Plan + Execute**를 실행했을 때 계획된 motion이 어떤 topic에 나타나는지 `rqt_graph`로 추적했다. 그 결과 `/display_planned_path`를 trajectory source로 사용할 수 있다고 판단했고, 이를 `JointTrajectory` 형태로 변환해 controller에 전달하는 구조를 구성했다.

* **Trajectory mirror node를 설계하고 단계적으로 개선했다.**

  * `kinova_mirror_node.py`
    초기 버전이다. `/eps_arm/cmd`를 구독한 뒤 joint name prefix를 처리하고, simulation controller와 real Kinova controller 양쪽으로 trajectory를 다시 발행한다.

  * `display_to_eps_cmd.py`
    팀원의 아이디어를 바탕으로 추가한 bridge node이다. MoveIt 2의 `DisplayTrajectory` message를 일반 `JointTrajectory`로 변환해 `/eps_arm/cmd`로 전달한다.

  * `eps_mirror_node.py`
    최종 버전인 MirrorNode v2이다. 위 두 기능을 하나의 node로 통합했다. MoveIt 2에서 들어오는 trajectory와 terminal에서 직접 입력하는 trajectory를 모두 받을 수 있으며, 이를 simulation Kinova와 real Kinova controller로 동시에 전달한다.

* **`robot.yaml` launch crash를 디버깅했다.**
  `robot.yaml` 설정으로 인해 launch 과정에서 crash가 발생했으며, 항목을 하나씩 제거하며 문제가 발생하는 지점을 좁혔다. 이후 안정적으로 동작하는 최소 설정을 다시 구성했다.

* **Simulation 및 real robot 실행용 launch 파일을 작성했다.**

  * `eps_sim.launch.py` — Gazebo simulation 실행용 launch file
  * `eps_kinova.launch.py` — 실물 Kinova Gen3 연결 및 실행용 launch file

* **실물 Kinova 연결용 bash script를 작성했다.**
  `eps_kinova_connect.sh` script를 작성해 PC 네트워크 설정, 로봇 연결 확인, ROS 2 workspace 환경 불러오기, real Kinova launch 실행 과정을 자동화했다.

* **팀 Setup Guide를 작성했다.**
  다음 EPS 기수 학생들이 동일한 환경을 재현할 수 있도록 simulation 실행, real Kinova 연결, troubleshooting 절차를 문서화했다.

프로젝트 중 겪은 주요 문제와 해결 과정은 [**TROUBLESHOOTING_KR.md**](./TROUBLESHOOTING_KR.md)에 정리했다.

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

> 참고: `.launch.py` 파일들은 Colcon workspace 안의 `eps_bringup` ROS 2 package 내부에 위치한다는 전제로 작성되었다. 아래 명령을 실행하려면 해당 파일들을 본인의 `eps_bringup` package 안에 배치해야 한다.

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

`eps_kinova_connect.sh` script는 PC 네트워크 설정, 로봇 연결 확인, ROS 2 workspace 환경 불러오기, `eps_kinova.launch.py` 실행까지 처리한다.

## 프로젝트 기간

2025-09-01 – 2025-12-18 · 30 ECTS · 한 학기 프로젝트

## License

본 저장소의 EPS custom code에는 MIT License를 적용한다.
외부 package와 문서는 각 원본 license를 따른다.
