"""Start a simulation-only motion path with no device or network transport."""

from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    parameters = PathJoinSubstitution([FindPackageShare("robotics_sim"), "config", "sim.yaml"])
    return LaunchDescription(
        [
            Node(
                package="robotics_sim", executable=executable,
                namespace="sim", parameters=[parameters],
            )
            for executable in ("safety_gate", "fake_base", "sim_environment")
        ]
    )
