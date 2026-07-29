# Control safety invariants / 控制安全不变量

1. Only one safety gate may issue a motion request to the base interface.
2. Commands carry bounded values and expire without a fresh request.
3. Emergency stop, critical diagnostics, stale command, and failed safety observation resolve to zero motion.
4. Recovery requires a documented reset and a safe-state check.
5. Simulation and fake transports are the default verification backends.
