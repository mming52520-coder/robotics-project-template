"""ROS 2 fake base that publishes synthetic odometry only."""

import math
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node

from robotics_sim.core import FakeBase


class FakeBaseNode(Node):
    def __init__(self) -> None:
        super().__init__("fake_base")
        self.base = FakeBase(self.declare_parameter("command_timeout_s", 0.2).value)
        self.create_subscription(Twist, "cmd_safe", self._command, 10)
        self.odom_pub = self.create_publisher(Odometry, "odom", 10)
        self.create_timer(0.05, self._step)

    def _command(self, message: Twist) -> None:
        self.base.receive_command(message.linear.x, message.angular.z, time.monotonic())

    def _step(self) -> None:
        linear, angular = self.base.step(time.monotonic())
        odom = Odometry()
        odom.header.stamp = self.get_clock().now().to_msg()
        odom.header.frame_id = "odom"
        odom.child_frame_id = "base_link"
        odom.pose.pose.position.x = self.base.x
        odom.pose.pose.position.y = self.base.y
        odom.pose.pose.orientation.z = math.sin(self.base.yaw / 2)
        odom.pose.pose.orientation.w = math.cos(self.base.yaw / 2)
        odom.twist.twist.linear.x = linear
        odom.twist.twist.angular.z = angular
        self.odom_pub.publish(odom)


def main() -> None:
    rclpy.init()
    node = FakeBaseNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
