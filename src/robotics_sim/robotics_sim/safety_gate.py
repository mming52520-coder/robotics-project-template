"""ROS 2 adapter for the simulation-only safety gate."""

import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from std_msgs.msg import Bool
from std_srvs.srv import Trigger

from robotics_sim.core import SafetyGate


class SafetyGateNode(Node):
    def __init__(self) -> None:
        super().__init__("safety_gate")
        self.gate = SafetyGate(
            max_linear=self.declare_parameter("max_linear_mps", 0.6).value,
            max_angular=self.declare_parameter("max_angular_radps", 1.0).value,
            command_timeout=self.declare_parameter("command_timeout_s", 0.25).value,
            status_timeout=self.declare_parameter("status_timeout_s", 0.3).value,
        )
        self.safe_pub = self.create_publisher(Twist, "cmd_safe", 10)
        self.create_subscription(Twist, "cmd_request", self._command, 10)
        self.create_subscription(Bool, "emergency_stop", self._estop, 10)
        self.create_subscription(Bool, "health_ok", self._health, 10)
        self.create_subscription(Bool, "obstacle_clear", self._obstacle, 10)
        self.create_service(Trigger, "reset_estop", self._reset)
        self.create_timer(0.05, self._publish)

    def _command(self, message: Twist) -> None:
        unused = (message.linear.y, message.linear.z, message.angular.x, message.angular.y)
        if any(value != 0.0 for value in unused) or not self.gate.receive_command(
            message.linear.x, message.angular.z, time.monotonic()
        ):
            self.gate.command = None
            self.gate.command_at = None
            self.get_logger().debug("Rejected invalid or unsafe motion request")

    def _estop(self, message: Bool) -> None:
        self.gate.receive_estop(message.data, time.monotonic())

    def _health(self, message: Bool) -> None:
        self.gate.receive_health(message.data, time.monotonic())

    def _obstacle(self, message: Bool) -> None:
        self.gate.receive_obstacle(message.data, time.monotonic())

    def _reset(self, _request: Trigger.Request, response: Trigger.Response) -> Trigger.Response:
        response.success = self.gate.reset_estop(time.monotonic())
        response.message = (
            "reset accepted; send a fresh command"
            if response.success else "inputs not healthy and fresh"
        )
        return response

    def _publish(self) -> None:
        linear, angular = self.gate.output(time.monotonic())
        message = Twist()
        message.linear.x = linear
        message.angular.z = angular
        self.safe_pub.publish(message)


def main() -> None:
    rclpy.init()
    node = SafetyGateNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
