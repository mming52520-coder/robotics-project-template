"""Deterministic motion gate and kinematic fake base, without ROS dependencies."""

from __future__ import annotations

import math


def _fresh(now: float, stamp: float | None, timeout: float) -> bool:
    return stamp is not None and 0.0 <= now - stamp <= timeout


class SafetyGate:
    """Allow bounded motion only while every simulated safety input is fresh."""

    def __init__(
        self, max_linear: float = 0.6, max_angular: float = 1.0,
        command_timeout: float = 0.25, status_timeout: float = 0.3,
    ) -> None:
        if not all(
            math.isfinite(value) and value > 0
            for value in (max_linear, max_angular, command_timeout, status_timeout)
        ):
            raise ValueError("limits and timeouts must be finite positive numbers")
        self.max_linear = max_linear
        self.max_angular = max_angular
        self.command_timeout = command_timeout
        self.status_timeout = status_timeout
        self.command: tuple[float, float] | None = None
        self.command_at: float | None = None
        self.estop: bool | None = None
        self.estop_at: float | None = None
        # A new process has no evidence that a previous emergency stop was cleared.
        self.estop_latched = True
        self.health: bool | None = None
        self.health_at: float | None = None
        self.obstacle_clear: bool | None = None
        self.obstacle_at: float | None = None

    def receive_command(self, linear: float, angular: float, now: float) -> bool:
        self._expire_stale_status(now)
        if not (
            math.isfinite(linear) and math.isfinite(angular)
            and abs(linear) <= self.max_linear and abs(angular) <= self.max_angular
            and not self.estop_latched and self._inputs_ready(now)
        ):
            self.command = None
            self.command_at = None
            return False
        self.command = (linear, angular)
        self.command_at = now
        return True

    def receive_estop(self, asserted: bool, now: float) -> None:
        self._expire_stale_status(now)
        self.estop = asserted
        self.estop_at = now
        if asserted:
            self.estop_latched = True
            self.command = None
            self.command_at = None

    def receive_health(self, healthy: bool, now: float) -> None:
        self._expire_stale_status(now)
        self.health = healthy
        self.health_at = now
        if not healthy:
            self.command = None
            self.command_at = None

    def receive_obstacle(self, clear: bool, now: float) -> None:
        self._expire_stale_status(now)
        self.obstacle_clear = clear
        self.obstacle_at = now
        if not clear:
            self.command = None
            self.command_at = None

    def _inputs_ready(self, now: float) -> bool:
        return (
            self.estop is False and _fresh(now, self.estop_at, self.status_timeout)
            and self.health is True and _fresh(now, self.health_at, self.status_timeout)
            and self.obstacle_clear is True and _fresh(now, self.obstacle_at, self.status_timeout)
        )

    def _expire_stale_status(self, now: float) -> None:
        estop_fresh = _fresh(now, self.estop_at, self.status_timeout)
        if not estop_fresh:
            self.estop_latched = True
        if not (
            estop_fresh
            and _fresh(now, self.health_at, self.status_timeout)
            and _fresh(now, self.obstacle_at, self.status_timeout)
        ):
            self.command = None
            self.command_at = None

    def reset_estop(self, now: float) -> bool:
        self._expire_stale_status(now)
        if not self._inputs_ready(now):
            return False
        self.estop_latched = False
        self.command = None
        self.command_at = None
        return True

    def output(self, now: float) -> tuple[float, float]:
        self._expire_stale_status(now)
        if (
            self.estop_latched or not self._inputs_ready(now)
            or not _fresh(now, self.command_at, self.command_timeout)
        ):
            return (0.0, 0.0)
        assert self.command is not None
        return self.command


class FakeBase:
    """Integrate a gated command in memory; there is no device transport."""

    def __init__(self, command_timeout: float = 0.2) -> None:
        if not math.isfinite(command_timeout) or command_timeout <= 0:
            raise ValueError("command timeout must be finite and positive")
        self.command_timeout = command_timeout
        self.command = (0.0, 0.0)
        self.command_at: float | None = None
        self.last_step: float | None = None
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0

    def receive_command(self, linear: float, angular: float, now: float) -> None:
        valid = math.isfinite(linear) and math.isfinite(angular)
        self.command = (linear, angular) if valid else (0.0, 0.0)
        self.command_at = now

    def step(self, now: float) -> tuple[float, float]:
        dt = 0.0 if self.last_step is None else max(0.0, min(now - self.last_step, 0.1))
        self.last_step = now
        fresh = _fresh(now, self.command_at, self.command_timeout)
        linear, angular = self.command if fresh else (0.0, 0.0)
        self.x += linear * math.cos(self.yaw) * dt
        self.y += linear * math.sin(self.yaw) * dt
        self.yaw += angular * dt
        return linear, angular
