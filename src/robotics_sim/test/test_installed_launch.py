"""Smoke-test the installed launch and separate ROS 2 node processes."""

import os
import signal
import subprocess
import tempfile
import time
import unittest

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from std_srvs.srv import Trigger


class InstalledLaunchTest(unittest.TestCase):
    def test_installed_graph_starts_at_zero(self) -> None:
        rclpy.init()
        probe = Node("installed_launch_probe")
        safe_commands: list[Twist] = []
        probe.create_subscription(Twist, "/sim/cmd_safe", safe_commands.append, 10)
        with tempfile.TemporaryFile(mode="w+t") as launch_log:
            process = subprocess.Popen(
                ["ros2", "launch", "robotics_sim", "sim.launch.py"],
                stdout=launch_log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            try:
                deadline = time.monotonic() + 10.0
                expected = {"safety_gate", "fake_base", "sim_environment"}
                while time.monotonic() < deadline:
                    rclpy.spin_once(probe, timeout_sec=0.1)
                    names = {
                        name for name, namespace in probe.get_node_names_and_namespaces()
                        if namespace == "/sim"
                    }
                    if expected <= names and safe_commands:
                        break
                    self.assertIsNone(
                        process.poll(), "installed launch exited before graph was ready"
                    )
                self.assertTrue(expected <= names, f"missing nodes: {expected - names}")
                self.assertTrue(safe_commands, "installed safety gate did not publish")
                self.assertEqual(safe_commands[-1].linear.x, 0.0)
                self.assertEqual(safe_commands[-1].angular.z, 0.0)
            except Exception:
                launch_log.seek(0)
                print(launch_log.read())
                raise
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGINT)
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait(timeout=5)
                probe.destroy_node()
                rclpy.shutdown()

    def test_gate_process_restart_requires_reset(self) -> None:
        rclpy.init()
        probe = Node("process_restart_probe")
        safe_commands: list[Twist] = []
        odometry: list[Odometry] = []
        probe.create_subscription(Twist, "/sim/cmd_safe", safe_commands.append, 10)
        probe.create_subscription(Odometry, "/sim/odom", odometry.append, 10)
        requests = probe.create_publisher(Twist, "/sim/cmd_request", 10)
        reset = probe.create_client(Trigger, "/sim/reset_estop")
        processes: list[subprocess.Popen] = []

        def start(executable: str, log) -> subprocess.Popen:
            process = subprocess.Popen(
                ["ros2", "run", "robotics_sim", executable, "--ros-args", "-r", "__ns:=/sim"],
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            processes.append(process)
            return process

        def stop(process: subprocess.Popen) -> None:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGINT)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)

        def pump(seconds: float) -> None:
            deadline = time.monotonic() + seconds
            while time.monotonic() < deadline:
                rclpy.spin_once(probe, timeout_sec=0.02)

        def send_motion() -> None:
            request = Twist()
            request.linear.x = 0.2
            requests.publish(request)

        def reset_gate() -> None:
            self.assertTrue(reset.wait_for_service(timeout_sec=3.0))
            future = reset.call_async(Trigger.Request())
            deadline = time.monotonic() + 3.0
            while not future.done() and time.monotonic() < deadline:
                rclpy.spin_once(probe, timeout_sec=0.05)
            self.assertTrue(future.done() and future.result().success)

        try:
            with tempfile.TemporaryFile(mode="w+t") as environment_log, tempfile.TemporaryFile(
                mode="w+t"
            ) as gate_log, tempfile.TemporaryFile(mode="w+t") as base_log:
                start("sim_environment", environment_log)
                start("fake_base", base_log)
                gate = start("safety_gate", gate_log)
                try:
                    deadline = time.monotonic() + 10.0
                    while not safe_commands and time.monotonic() < deadline:
                        pump(0.1)
                        self.assertIsNone(gate.poll())
                    self.assertTrue(safe_commands)
                    pump(0.3)
                    reset_gate()
                    for _ in range(20):
                        send_motion()
                        pump(0.05)
                        if safe_commands[-1].linear.x == 0.2:
                            break
                    self.assertEqual(safe_commands[-1].linear.x, 0.2)
                    pump(0.1)
                    self.assertTrue(odometry)
                    self.assertEqual(odometry[-1].twist.twist.linear.x, 0.2)

                    stop(gate)
                    pump(0.35)
                    self.assertEqual(odometry[-1].twist.twist.linear.x, 0.0)
                    safe_commands.clear()
                    gate = start("safety_gate", gate_log)
                    deadline = time.monotonic() + 10.0
                    while not safe_commands and time.monotonic() < deadline:
                        pump(0.1)
                        self.assertIsNone(gate.poll())
                    self.assertTrue(safe_commands)
                    for _ in range(10):
                        send_motion()
                        pump(0.05)
                        self.assertEqual(safe_commands[-1].linear.x, 0.0)
                    reset_gate()
                    for _ in range(20):
                        send_motion()
                        pump(0.05)
                        if safe_commands[-1].linear.x == 0.2:
                            break
                    self.assertEqual(safe_commands[-1].linear.x, 0.2)
                except Exception:
                    environment_log.seek(0)
                    gate_log.seek(0)
                    base_log.seek(0)
                    print(environment_log.read(), gate_log.read(), base_log.read())
                    raise
        finally:
            for process in reversed(processes):
                stop(process)
            probe.destroy_node()
            rclpy.shutdown()
