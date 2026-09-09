# 설치와 실행 범위

## 장비 없이 코드 확인

Python 3.10 이상에서 저장소 루트에서 실행합니다. ROS2 설치가 필요하지 않습니다.

```sh
python -m unittest discover -s tests -v
```

관절명·배열 길이·유한값·시간 순서, 입력 보존, 실물 출력 분기를 검사합니다. wrapper 테스트는 ROS2 메시지와 publisher의 메모리 대역을 사용하므로 DDS 통신이나 실제 controller 수신을 확인하는 테스트가 아닙니다.

## ROS2 환경

당시 환경은 Ubuntu 24.04 / ROS2 Jazzy, MoveIt2, Gazebo의 Clearpath 패키지, Kinova Kortex였습니다. 정확한 의존 패키지 commit은 고정되어 있지 않습니다. 이번 버전은 **라우터 패키지만** 제공합니다. 드라이버·Gazebo·로봇 모델·controller는 별도로 준비해야 합니다.

ROS2 Jazzy가 설치된 Ubuntu에서:

```sh
source /opt/ros/jazzy/setup.bash
mkdir -p ~/eps_ws/src
cd ~/eps_ws/src
git clone https://github.com/CHOI-HYOJUN-kr/eps-mirror-node.git
cd ~/eps_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select eps_mirror
source install/setup.bash
ros2 launch eps_mirror mirror.launch.py
```

위 명령은 이 저장소의 **0.2.0 패키지 구성**을 기준으로 합니다. 이전의 노드 파일만 있는 스냅샷에는 적용되지 않습니다. 로컬 복사본으로 검토할 때에는 이 폴더를 `~/eps_ws/src/eps-mirror-node`에 복사해 clone 단계를 대신합니다. 패키지의 resource marker·package.xml·설치 entry point 구성은 [ROS2 Jazzy 패키지 안내](https://docs.ros.org/en/jazzy/How-To-Guides/Developing-a-ROS-2-Package.html)를 따릅니다.

기본값은 simulation 출력만 활성화합니다. Gazebo와 controller를 먼저 실행한 상태에서 라우터가 토픽을 구독합니다. MoveIt의 **Plan만 눌러도 display 토픽이 입력될 수 있어 simulation이 움직일 수 있습니다.**

| 파라미터 | 기본값 | 의미 |
| --- | --- | --- |
| enable_sim | true | simulation controller로 출력 |
| enable_real | false | 실물 controller publisher 생성·명령 출력 |
| allow_display_to_real | false | display 계획도 실물 출력에 허용; enable_real이 함께 필요 |
| display_topic | /display_planned_path | 계획 입력 |
| cmd_topic | /eps_arm/cmd | 명시적 JointTrajectory 입력 |

실물 controller 연결과 관절·clock 기준을 확인한 후, 명시적 command 경로만 활성화하려면:

```sh
ros2 launch eps_mirror mirror.launch.py enable_sim:=false enable_real:=true
```

이 명령 자체가 Kortex 드라이버를 시작하지는 않습니다. display는 실물에 전달되지 않습니다. 당시처럼 display에서 실물까지 전달하려면 `allow_display_to_real:=true`도 설정해야 하지만, 현재 유지보수 버전의 장비 재시험은 수행하지 않았습니다.

## 원본 대비 제약

입력은 Kinova 7개 관절의 완전한 position 궤적만 받습니다. `trajectory[0]`만 사용하고 나머지 segment는 경고 후 무시합니다. positions의 단위와 관절 순서·기구학적 대응은 환경에서 확인해야 합니다. joint limit, 충돌, 최신성, 실행 완료를 검사하는 기능은 없습니다. header와 time_from_start를 유지하므로 simulation과 실물 clock 기준이 다른 경우 별도 검토가 필요합니다.

`scripts/eps_kinova_connect.sh`는 `ROBOT_IP`를 명시한 경우에만 주소 표시와 ping을 합니다. 네트워크 주소 변경·방화벽 해제·실물 launch는 수행하지 않습니다.

[프로젝트로 돌아가기](../README.md)
