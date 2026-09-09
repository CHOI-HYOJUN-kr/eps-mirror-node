"""Start only the router. Drivers and simulators are separate prerequisites."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    arguments = [
        DeclareLaunchArgument("enable_sim", default_value="true"),
        DeclareLaunchArgument("enable_real", default_value="false"),
        DeclareLaunchArgument("allow_display_to_real", default_value="false"),
    ]
    return LaunchDescription(arguments + [Node(
        package="eps_mirror", executable="mirror_node", output="screen",
        parameters=[{name: ParameterValue(LaunchConfiguration(name), value_type=bool)
                     for name in ("enable_sim", "enable_real", "allow_display_to_real")}],
    )])
