# Mobile Collaborative Robot

EPS Fall 2025 — Team BOB
LGP Research Lab (ENIT · UTTOP), France

Clearpath Ridgeback 모바일 베이스와 Kinova Gen3 7-DOF 암을 ROS 2 Jazzy
환경에서 통합하여, 동일한 MoveIt 2 trajectory를 시뮬레이션(Gazebo)과
실물 로봇 양쪽에서 동시에 실행하도록 만든 프로젝트입니다.

## 본인 기여 (Hyojun Choi)

Kinova Gen3 측 담당. `MirrorNode v2`(시뮬↔실물 trajectory 라우팅)의
구조를 제안·구현했고, 통합 launch 파일과 연결 스크립트, `robot.yaml`
안정화, Gazebo→실물 trajectory 동치 검증을 진행했습니다. Setup Guide
작성·정리에도 참여했습니다. 자세한 문제 정의·시행착오·해결 과정은
[**TROUBLESHOOTING.md**](./TROUBLESHOOTING.md)에 정리되어 있습니다.

## 폴더 구조

| 폴더 | 내용 |
| --- | --- |
| `src/` | ROS 2 노드 (`mirror_node.py`, `display_to_eps_cmd.py` 등) |
| `launch/` | 시뮬레이션·실물 bring-up launch 파일 |
| `scripts/` | 실물 Kinova 연결용 bash 스크립트 |
| `config/` | `robot.yaml` (Clearpath 로봇 구성) |
| `assets/` | 그래프, TF 트리, 데모 영상 |
| `docs/` | 팀 단위 보고서 (Final Document, Setup Guide, 요약본 등) |

## 환경

- ROS 2 Jazzy
- Gazebo (Clearpath simulation packages)
- MoveIt 2
- Kinova Kortex ROS 2 driver

## 실행

```bash
# 시뮬레이션
ros2 launch eps_bringup eps_sim.launch.py

# 실물 Kinova
bash scripts/eps_kinova_connect.sh
ros2 launch eps_bringup eps_kinova.launch.py
```

## 기간 / 학점

2025-09-01 – 2025-12-18 · 30 ECTS · 한 학기
