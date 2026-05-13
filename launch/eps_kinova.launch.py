# ===================================================================
#  EPS Real Kinova Bringup (eps_kinova.launch.py)
#
#  Developed by Team BOB
#  Date: 2025-12-01
#
#  Description:
#    - Launches the physical Kinova Gen3 using the Kortex driver
#    - Starts MirrorNode v2, which:
#         * Subscribes to MoveIt planned trajectories
#         * Converts them to JointTrajectory
#         * Sends commands to:
#               - Physical Kinova Gen3
#               - Gazebo-simulated Gen3, if the simulation is running
#
#  Note:
#    The default robot IP is set for our lab setup.
#    Change the robot_ip launch argument if your Kinova uses a different IP.
# ===================================================================

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # ------------------------------------------------------------
    # Launch arguments
    # ------------------------------------------------------------
    robot_ip_arg = DeclareLaunchArgument(
        "robot_ip",
        default_value="192.168.1.10",
        description="IP address of the physical Kinova Gen3 controller"
    )

    dof_arg = DeclareLaunchArgument(
        "dof",
        default_value="7",
        description="Degrees of freedom of the Kinova arm"
    )

    # ------------------------------------------------------------
    # 1) Physical Kinova Gen3 Driver (Kortex)
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
            "robot_ip": LaunchConfiguration("robot_ip"),
            "dof": LaunchConfiguration("dof"),
            "use_internal_bus_gripper_comm": "false",
            "launch_rviz": "false",
        }.items()
    )

    # ------------------------------------------------------------
    # 2) MirrorNode v2
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
            "real_topic": "/joint_trajectory_controller/joint_trajectory",
        }]
    )

    return LaunchDescription([
        robot_ip_arg,
        dof_arg,
        kortex_launch,
        mirror_node,
    ])
