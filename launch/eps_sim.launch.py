# ===============================================================
#  EPS Simulation Launch File (eps_sim.launch.py)
#  Created: 25-11-2025
#  Author: Team BOB
#
#  Detailed Technical Concept
#  -------------------------------------------------------------
#  Purpose:
#    This launch file brings up the full simulation environment used
#    in the EPS project. It initializes:
#
#       1) Gazebo simulation for the Ridgeback + Kinova platform
#       2) Localization system (AMCL)
#       3) Required TF frames (map → odom)
#       4) Nav2 navigation stack
#       5) cmd_vel relay for platform motion control
#
#    This mirrors the real-robot stack but entirely in simulation,
#    enabling testing, debugging, algorithm development, and
#    demonstration without requiring the physical robot.
#
#  Simulation Pipeline:
#        ┌────────────────────────────────────────────────┐
#        │              Gazebo Simulation                 │
#        │  - Loads robot model from robot.yaml           │
#        │  - Publishes sensor + TF data                  │
#        └───────────────┬────────────────────────────────┘
#                        │
#                        ▼
#        ┌────────────────────────────────────────────────┐
#        │               Localization (AMCL)              │
#        │  - Uses /scan + odometry                      │
#        │  - Outputs robot_pose → map frame             │
#        └───────────────┬────────────────────────────────┘
#                        │
#                        ▼
#        ┌────────────────────────────────────────────────┐
#        │               Nav2 Stack                       │
#        │  - Global planner / local planner              │
#        │  - Behavior tree for autonomous navigation     │
#        └───────────────┬────────────────────────────────┘
#                        │
#                        ▼
#        ┌────────────────────────────────────────────────┐
#        │ cmd_vel Relay                                 │
#        │  - Forwards smoothed navigation velocity to    │
#        │    robot platform controller                   │
#        └────────────────────────────────────────────────┘
#
#  Why this launch file exists:
#    - To create a **complete simulation equivalent** of the real robot stack.
#    - To enable development and testing of:
#         • autonomous navigation (Nav2)
#         • localization (AMCL)
#         • TF frame correctness
#         • motion interface through cmd_vel
#    - To ensure the same architecture used on real hardware is first
#      validated in simulation, avoiding unsafe real-world testing.
#
#  Result:
#    Running this launch file provides a fully operational simulated
#    Ridgeback + Kinova platform ready for navigation, mapping,
#    and integration with higher-level EPS modules.
# ===============================================================

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    home = os.path.expanduser('~')
    clearpath_setup = os.path.join(home, 'clearpath')
    robot_yaml = os.path.join(clearpath_setup, 'robot.yaml')

    # -----------------------------------------------------------
    # A) Gazebo Simulation
    # -----------------------------------------------------------
    # Loads the Clearpath simulation environment:
    #   - Generates the robot from robot.yaml configuration
    #   - Starts physics, sensors, controllers
    #   - Provides simulated TF and sensor topics
    #
    # robot.yaml controls:
    #   - base model
    #   - sensors (lidar, IMU, depth camera)
    #   - top-mounted Kinova Gen3 arm (if enabled)
    #
    # This forms the foundation for all simulated behavior.
    # -----------------------------------------------------------
    sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('clearpath_gz'),
                'launch',
                'simulation.launch.py'
            )
        ),
        launch_arguments={
            'config': robot_yaml
        }.items()
    )

    # -----------------------------------------------------------
    # B) Localization (AMCL)
    # -----------------------------------------------------------
    # Responsibilities:
    #   - Performs probabilistic localization in a 2D map
    #   - Uses:
    #       • Laser scan (/scan)
    #       • Odometry data
    #   - Publishes /amcl_pose
    #
    # use_sim_time=true:
    #   - Ensures Nav2 + AMCL run on simulated clock
    # -----------------------------------------------------------
    localization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('clearpath_nav2_demos'),
                'launch',
                'localization.launch.py'
            )
        ),
        launch_arguments={
            'setup_path': clearpath_setup,
            'use_sim_time': 'true'
        }.items()
    )

    # -----------------------------------------------------------
    # C) Static TF: map → odom
    # -----------------------------------------------------------
    # Why needed?
    #   - Many navigation systems assume map → odom exists.
    #   - Usually AMCL publishes this, but in simulation the transform
    #     needs to be explicitly created and fed into the robot’s namespace.
    #
    # Remapping /tf & /tf_static:
    #   - Gazebo robots often use a namespace (e.g., /r100_0000)
    #   - This ensures the transform is published into the correct TF tree.
    # -----------------------------------------------------------
    static_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='map_to_odom',
        arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom'],
        remappings=[
            ('/tf', '/r100_0000/tf'),
            ('/tf_static', '/r100_0000/tf_static'),
        ]
    )

    # -----------------------------------------------------------
    # D) Nav2 (Navigation Stack)
    # -----------------------------------------------------------
    # Responsibilities:
    #   - Global planner: map-based path planning
    #   - Local planner: obstacle avoidance + real-time control
    #   - BT navigator: high-level behavior tree for navigation tasks
    #
    # use_sim_time=true:
    #   - Ensures that all Nav2 timers and planning align with Gazebo clock
    # -----------------------------------------------------------
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('clearpath_nav2_demos'),
                'launch',
                'nav2.launch.py'
            )
        ),
        launch_arguments={
            'use_sim_time': 'true'
        }.items()
    )

    # -----------------------------------------------------------
    # E) cmd_vel Relay
    # -----------------------------------------------------------
    # Nav2 produces:
    #     /r100_0000/cmd_vel_smoothed
    #
    # The robot platform expects:
    #     /r100_0000/platform/cmd_vel
    #
    # This relay:
    #   - Bridges those topics
    #   - Ensures the simulated platform moves exactly as Nav2 commands
    #
    # Without this relay, the robot would plan paths but NOT move.
    # -----------------------------------------------------------
    cmd_vel_relay = Node(
        package='topic_tools',
        executable='relay',
        name='cmd_vel_relay',
        arguments=[
            '/r100_0000/cmd_vel_smoothed',
            '/r100_0000/platform/cmd_vel'
        ]
    )

    return LaunchDescription([
        sim_launch,
        localization_launch,
        static_tf,
        nav2_launch,
        cmd_vel_relay,
    ])


