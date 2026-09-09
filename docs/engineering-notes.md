# 메시지 경로와 수정 판단

## 입력과 출력

| 경계 | 메시지 | 처리 |
| --- | --- | --- |
| `/display_planned_path` | `moveit_msgs/DisplayTrajectory` | `trajectory[0].joint_trajectory` 사용 |
| `/eps_arm/cmd` | `trajectory_msgs/JointTrajectory` | 직접 입력 |
| simulation controller | `JointTrajectory` | `joint_1` → `arm_0_joint_1` |
| real controller | `JointTrajectory` | `arm_0_joint_1` → `joint_1` |

관절 순서를 바꾸지 않고 positions·velocities·accelerations·effort·시간을 그대로 복사합니다. 이 방식은 양쪽 관절의 순서, 단위와 물리적 의미가 대응한다는 전제에 의존합니다. 이름이 같다는 이유만으로 기구학적 호환성을 보장하지 않습니다.

## 시도와 결정

1. 초기 mirror는 터미널 명령을 두 controller로 분배했습니다.
2. 팀원이 제안한 display 토픽을 분석해 bridge를 추가했습니다.
3. 두 기능을 MirrorNode v2에 통합해 입력과 변환을 한 곳에서 확인했습니다.

두 번 발행했다는 로그는 두 로봇이 완료했다는 뜻이 아닙니다. 당시 노드는 실행 피드백이나 action result를 받지 않았고, 지연·동기화 오차도 측정하지 않았습니다.

## 환경 문제를 좁힌 방법

Rolling에서 프로젝트의 Clearpath 구성이 불안정해 Jazzy로 옮기는 방향을 제안했습니다. 이는 모든 Rolling 패키지가 불안정하다는 평가가 아닙니다. 결합 모델은 부품을 하나씩 제거·복원하며 Kinova와 IMU를 포함하는 구성을 찾았습니다. LiDAR 플러그인은 해결하지 못했습니다.

현재 공개 준비본은 검증되지 않은 Nav2/AMCL 통합을 자동 실행하는 예전 launch를 제거했습니다. 원본은 기존 커밋에 남으며 변경 이유는 [maintenance](maintenance.md)에 기록합니다.

[프로젝트로 돌아가기](../README.md)
