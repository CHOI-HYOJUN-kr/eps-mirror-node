# Mobile Collaborative Robot

EPS Fall 2025 — Team BOB
ENIT, Tarbes, France · LGP Lab (UTTOP) 의뢰 프로젝트

시뮬레이션 Clearpath Ridgeback 모바일 베이스와 Kinova Gen3 7-DOF 매니퓰레이터를 통합하고, 동일한 MoveIt 2 trajectory를 Gazebo 시뮬레이션 Kinova와 실물 Kinova Gen3 양쪽에서 검증하기 위한 ROS 2 Jazzy 스택입니다.

![Demo](../assets/eps_demo.gif)

> English version · [README](../README.md) · [TROUBLESHOOTING](../TROUBLESHOOTING.md)

## 담당 기여 (최효준)

저는 Kinova Gen3 통합 측면을 담당했으며, 구체적으로는 sim-to-real trajectory 라우팅 아키텍처 설계, joint 이름 정규화, `rqt_graph` 기반 MoveIt 2 토픽 분석, launch 파일 통합, 실물 로봇 연결 워크플로우를 맡았습니다.

이번이 첫 로봇 프로젝트였기 때문에 학기 중에 ROS 2를 학습하며 진행했습니다. 코드 초안 작성 속도를 높이기 위해 AI 도구를 활용했으나, 아키텍처 설계, 토픽 선정, 메시지 흐름 검증, Gazebo 우선 테스트, 실물 로봇 검증은 모두 제가 직접 수행했습니다.

구체적으로 한 일:

- **Sim ↔ Real 불일치 발견.** Ridgeback에 마운트된 시뮬레이션 Kinova와 실물 Kinova가 서로 다른 joint 이름 prefix(`arm_0_joint_X` vs `joint_X`)와 **서로 다른** controller namespace(`/r100_0000/arm_0_joint_trajectory_controller/...` vs `/joint_trajectory_controller/...`)를 사용하고 있다는 점을 확인했습니다. 이를 팀에 공유한 뒤, 두 문제를 한 번에 해결하는 가장 깔끔한 방법으로 custom ROS 2 노드를 만들기로 합의했습니다.

- **Mirror 대상 MoveIt 2 토픽 선정.** MoveIt 2는 다수의 토픽을 발행합니다. RViz에서 **Plan**과 **Plan + Execute**를 눌렀을 때 계획된 motion이 어디에 나타나는지 `rqt_graph`로 추적했고, `JointTrajectory`로 변환해 양쪽 controller로 라우팅할 수 있는 실용적인 trajectory source로 `/display_planned_path`를 선정했습니다.

- **노드 설계 및 3차례 반복 개선:**
  - `kinova_mirror_node.py` — v1. `/eps_arm/cmd`를 구독하고, 적절한 prefix 처리를 거쳐 sim과 real 양쪽으로 재발행.
  - `display_to_eps_cmd.py` — 팀원의 아이디어를 바탕으로 이후 추가한 bridge 노드. MoveIt의 `DisplayTrajectory`를 `/eps_arm/cmd` 상의 일반 `JointTrajectory`로 변환.
  - `eps_mirror_node.py` (MirrorNode v2) — 위 두 기능을 단일 노드로 통합. 두 입력 중 어느 쪽이든 받아서 sim과 real로 동시 라우팅.

- **`robot.yaml` 크래시 디버깅.** 항목을 하나씩 제거해 launch가 더 이상 크래시하지 않는 지점까지 좁힌 뒤, 안정적인 최소 설정을 다시 구성했습니다.

- **통합 launch 파일 작성** (`eps_sim.launch.py`, `eps_kinova.launch.py`) 및 실물 로봇 연결 전 호스트를 준비시키는 **네트워크 설정 bash 스크립트** (`eps_kinova_connect.sh`) 작성.

- **팀 Setup Guide 작성** — 다음 EPS 학기 학생들이 환경을 재현할 수 있도록.

발생한 문제들과 해결 과정의 상세 기록은 [**TROUBLESHOOTING_KR.md**](./TROUBLESHOOTING_KR.md) 참조.

## 노드 아키텍처

```
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
| `src/` | ROS 2 노드: `eps_mirror_node.py` (MirrorNode v2), `display_to_eps_cmd.py` (bridge), `kinova_mirror_node.py` (v1) |
| `launch/` | `eps_sim.launch.py` (시뮬레이션), `eps_kinova.launch.py` (실물 로봇) |
| `scripts/` | `eps_kinova_connect.sh` — 실물 Kinova용 호스트 네트워크 설정 자동화 |
| `config/` | `robot.yaml` (Clearpath 로봇 description) |
| `assets/` | `rosgraph(final).png`, `TF tree.pdf`, `eps_demo.gif` |
| `docs/` | 한국어 문서 (README, TROUBLESHOOTING, 프로젝트 요약본) |

> 참고: `.launch.py` 파일들은 Colcon 워크스페이스 내 `eps_bringup`이라는 ROS 2 패키지 안에 위치하는 것을 전제로 작성됐습니다. 아래 명령을 실행하려면 본인의 `eps_bringup` 패키지 안에 배치하시면 됩니다.

## 환경

- Ubuntu 24.04
- ROS 2 Jazzy
- Gazebo (Clearpath 시뮬레이션 패키지)
- MoveIt 2
- Kinova Kortex ROS 2 드라이버

## 실행

```bash
# 시뮬레이션
ros2 launch eps_bringup eps_sim.launch.py

# 실물 Kinova
bash scripts/eps_kinova_connect.sh
```

`eps_kinova_connect.sh` 스크립트는 호스트 네트워크 설정, 로봇 연결 검증, ROS 2 워크스페이스 source, `eps_kinova.launch.py` 실행까지 처리합니다.

## 프로젝트 기간

2025-09-01 – 2025-12-18 · 30 ECTS · 한 학기

## License

본 저장소의 EPS 커스텀 코드에 대해서는 MIT.
서드파티 패키지와 문서는 각자의 원본 라이센스를 따릅니다.
