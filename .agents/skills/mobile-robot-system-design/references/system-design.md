# System design reference / 系统设计参考

Use a ROS 2 reference architecture with one-way control authority:

```text
mission manager -> navigation -> safety gate -> base interface
                         ^             ^
                    localization    diagnostics
```

Every message contract states units, coordinate frame, timestamp freshness, owner, and expiry behavior. A stale command must resolve to zero motion. Keep simulation and fake transports behind the same base interface used by motion logic.
