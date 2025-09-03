# Context: GO2 Lab Sim (Isaac Sim 5.0 + Isaac Lab 2.2)

Flow:
1) Launch Isaac Sim 5.0 GUI (script or extension).
2) Load/create warehouse stage and spawn GO2.
3) Teleoperate with keyboard/gamepad. No ROS 2/bridge.
4) Record dataset via isaacsim.replicator.writers to output/<date-time>.
5) Preview Isaac Lab 2.2 task for rollouts and config validation.

Namespace rules:
- Use isaacsim.core.api, isaacsim.core.nodes. Avoid omni.isaac.* and omni.replicator.isaac.
- Use isaacsim.sensors.* and isaacsim.replicator.* for sensors/recording.
- Use isaacsim.storage.native and isaacsim.core.cloner for storage/duplication.
- Keep OmniGraph Compute Mode = On Demand to avoid OnSimulationStep warnings.

Definition of Done (DoD):
- GUI opens, warehouse visible, >= 240 frames step.
- GO2 spawns and moves with keyboard control (clamp/brake).
- Dataset saved under output/ with JSON meta.
- No OnSimulationStep warnings (On Demand).
- Lab 2.2 task preview steps without ROS.
