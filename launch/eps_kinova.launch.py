# ===================================================================
#  EPS Real Kinova Bringup (eps_kinova.launch.py)
#
#  Developed by Team BOB
#  Date: 2025-12-01
#
#  Description:
#    - Launches the real Kinova Gen3 using Kortex driver
#    - Starts a unified mirror_node that:
#         * Subscribes to MoveIt planned trajectories
#         * Converts them to JointTrajectory
#         * Sends commands simultaneously to:
#               - Real Kinova Gen3
#               - Gazebo simulated Gen3 (if running)
#
#    Clean, minimal, and fully aligned with eps_sim.launch.py style.
# ===================================================================

import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    # ------------------------------------------------------------
    # 1) Real Kinova Gen3 Driver (Kortex)
    # ------------------------------------------------------------
    kortex_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("kortex_bringup"),
                "launch",
                "gen3.launch.py"
            )
        ),
        launch_arguments={
            "robot_ip": "192.168.1.10",
            "dof": "7",
            "use_internal_bus_gripper_comm": "false",
            "launch_rviz": "false"
        }.items()
    )

    # ------------------------------------------------------------
    # 2) Unified Mirror Node
    # ------------------------------------------------------------
    mirror_node = Node(
        package="eps_mirror",
        executable="mirror_node",
        name="mirror_node",
        output="screen",
        parameters=[{
            "display_topic": "/display_planned_path",
            "cmd_topic": "/eps_arm/cmd",
            "sim_topic": "/r100_0000/arm_0_joint_trajectory_controller/joint_trajectory",
            "real_topic": "/joint_trajectory_controller/joint_trajectory"
        }]
    )

    return LaunchDescription([
        kortex_launch,
        mirror_node
    ])

