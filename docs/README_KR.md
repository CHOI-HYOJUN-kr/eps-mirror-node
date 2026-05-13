# Mobile Collaborative Robot

EPS Fall 2025 — Team BOB  
ENIT, Tarbes, France · LGP Lab (UTTOP) 의뢰 프로젝트

시뮬레이션상의 Clearpath Ridgeback 모바일 베이스와 Kinova Gen3 7-DOF 매니퓰레이터를 통합하고, 동일한 MoveIt 2 trajectory를 Gazebo 시뮬레이션 Kinova와 실물 Kinova Gen3 양쪽에서 검증하기 위해 구축한 ROS 2 Jazzy 기반 스택입니다.

![Demo](../assets/eps_demo.gif)

> English version · [README](../README.md) · [TROUBLESHOOTING](../TROUBLESHOOTING.md)

## 담당 기여 (최효준)

저는 Kinova Gen3 통합 파트를 담당했습니다. 구체적으로는 sim-to-real trajectory 라우팅 아키텍처, joint 이름 정규화, `rqt_graph`를 활용한 MoveIt 2 토픽 분석, launch 파일 통합, 실물 로봇 연결 워크플로우를 맡았습니다.

이 프로젝트는 제가 처음 수행한 로봇 프로젝트였습니다. 그래서 학기 중에 ROS 2를 처음부터 학습하며 진행했습니다. 코드 초안 작성 속도를 높이기 위해 AI 도구를 활용했지만, 아키텍처 설계, 토픽 선정, 메시지 흐름 검증, Gazebo 우선 테스트, 실물 로봇 검증은 제가 직접 수행했습니다.

구체적으로 수행한 작업은 다음과 같습니다.

- **Sim ↔ Real 불일치 문제를 발견했습니다.**Ridgeback에 마운트된 시뮬레이션 Kinova와 실물 Kinova는 서로 다른 joint 이름 prefix(`arm_0_joint_X` vs `joint_X`)와 서로 다른 controller namespace(`/r100_0000/arm_0_joint_trajectory_controller/...` vs `/joint_trajectory_controller/...`)를 사용하고 있었습니다. 이 문제를 팀에 공유했고, 두 문제를 동시에 해결하기 위해 custom ROS 2 node를 두는 방식이 가장 깔끔하다고 판단해 팀과 합의했습니다.

- **Mirror 대상으로 사용할 MoveIt 2 토픽을 선정했습니다.** MoveIt 2는 여러 토픽을 발행합니다. 저는 RViz에서 **Plan**과 **Plan + Execute**를 눌렀을 때 계획된 motion이 어디에 나타나는지 `rqt_graph`로 추적했습니다. 그 결과 `/display_planned_path`를 양쪽 controller로 라우팅하기에 적합한 trajectory source로 선정했고, 이를 `JointTrajectory`로 변환해 사용할 수 있도록 구성했습니다.

- **노드를 설계하고 세 차례에 걸쳐 개선했습니다.**
  - `kinova_mirror_node.py` — v1. `/eps_arm/cmd`를 구독하고, prefix 처리를 거쳐 sim과 real controller 양쪽으로 다시 발행합니다.
  - `display_to_eps_cmd.py` — 팀원의 아이디어를 바탕으로 이후 추가한 bridge node입니다. MoveIt의 `DisplayTrajectory`를 일반 `JointTrajectory`로 변환해 `/eps_arm/cmd`로 보냅니다.
  - `eps_mirror_node.py` (MirrorNode v2) — 위 두 기능을 하나의 node로 통합했습니다. MoveIt에서 들어오는 입력과 terminal에서 직접 들어오는 입력을 모두 받을 수 있으며, 이를 sim과 real controller로 동시에 라우팅합니다.

- **`robot.yaml` crash를 디버깅했습니다.** 항목을 하나씩 제거하며 launch crash가 멈추는 지점을 좁혔고, 이후 안정적으로 동작하는 최소 설정을 다시 구성했습니다.

- **통합 launch 파일**인 `eps_sim.launch.py`, `eps_kinova.launch.py`와, 실물 로봇 연결 전 host network를 설정하는 **bash script**인 `eps_kinova_connect.sh`를 작성했습니다.

- 다음 EPS 기수 학생들이 동일한 환경을 재현할 수 있도록 **팀 Setup Guide를 작성했습니다.**

프로젝트 중 겪은 문제와 해결 과정은 [**TROUBLESHOOTING_KR.md**](./TROUBLESHOOTING_KR.md)에 자세히 정리했습니다.

## 노드 아키텍처

```text
MoveIt (RViz Plan / Plan+Execute)        터미널 명령
            ↓                                   ↓
   /display_planned_path           /eps_arm/cmd (JointTrajectory)
            └───────────────┬───────────────────┘
                            ↓
                    [ MirrorNode v2 ]
                   (eps_mirror_node.py)
                       ↓           ↓
              Gazebo sim         실물 Kinova Gen3
            (arm_0_joint_X)         (joint_X)
```

## 저장소 구조

| 폴더 | 내용 |
| --- | --- |
| `src/` | ROS 2 nodes: `eps_mirror_node.py` (MirrorNode v2), `display_to_eps_cmd.py` (bridge), `kinova_mirror_node.py` (v1) |
| `launch/` | `eps_sim.launch.py` (simulation), `eps_kinova.launch.py` (real robot) |
| `scripts/` | `eps_kinova_connect.sh` — 실물 Kinova용 host network 설정 자동화 |
| `config/` | `robot.yaml` (Clearpath robot description) |
| `assets/` | `rosgraph(final).png`, `TF tree.pdf`, `eps_demo.gif` |
| `docs/` | 한국어 문서: README, TROUBLESHOOTING, 프로젝트 요약본 |

> 참고: `.launch.py` 파일들은 Colcon workspace 안의 `eps_bringup`이라는 ROS 2 package 내부에 위치한다는 전제로 작성되었습니다. 아래 명령을 실행하려면 해당 파일들을 본인의 `eps_bringup` package 안에 배치해야 합니다.

## 환경

- Ubuntu 24.04
- ROS 2 Jazzy
- Gazebo (Clearpath simulation packages)
- MoveIt 2
- Kinova Kortex ROS 2 driver

## 실행

```bash
# Simulation
ros2 launch eps_bringup eps_sim.launch.py

# Real Kinova
bash scripts/eps_kinova_connect.sh
```

`eps_kinova_connect.sh` script는 host network 설정, robot connection 확인, ROS 2 workspace source, `eps_kinova.launch.py` 실행까지 처리합니다.

## 프로젝트 기간

2025-09-01 – 2025-12-18 · 30 ECTS · 한 학기 프로젝트

## License

본 저장소의 EPS custom code에는 MIT License를 적용합니다.  
Third-party package와 document는 각자의 original license를 따릅니다.
