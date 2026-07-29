# Interface contracts / 接口契约

Every DesignPackage interface records an owner, producer, consumer, data meaning, unit, frame, timestamp/freshness rule, and failure behavior.

每个 DesignPackage 接口必须记录所有者、生产者、消费者、数据含义、单位、坐标系、时间戳或新鲜度规则，以及失效行为。

| Interface role / 接口角色 | Minimum contract / 最小契约 | Safe failure / 安全失效 |
|---|---|---|
| Motion request / 运动请求 | bounded linear and angular velocity, units, expiry | zero motion |
| Pose estimate / 位姿估计 | frame, timestamp, uncertainty | degraded localization |
| Observation / 观测 | coverage, timestamp, confidence | reduce speed or stop |
| Diagnostics / 诊断 | health state, freshness, severity | inhibit autonomous motion |

Never silently convert units, frames, or ownership. Record an unresolved conversion as an open decision and keep physical output disabled.

不得静默转换单位、坐标系或控制权。未解决的转换必须记录为待决项，并保持物理输出禁用。
