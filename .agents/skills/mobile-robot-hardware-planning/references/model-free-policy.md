# Model-free hardware policy / 型号无关硬件政策

Describe what a subsystem must do, how well it must do it, how it reports health, and what happens when it degrades. Keep the public DesignPackage model-free. A separate local selection list may compare real candidates when requirements permit; keep it under ignored `config/private/` and cite current manufacturer evidence. Follow `docs/reference/hardware-protocol-handoff.md` for its review fields.

Use functional phrases such as "timestamped motion feedback" or "obstacle observation covering the stopping envelope". Record procurement, electrical approval, and installation measurements as open decisions until separately reviewed.
