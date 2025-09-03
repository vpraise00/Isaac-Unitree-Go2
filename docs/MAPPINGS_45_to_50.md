# API Namespace Mappings (4.5/1.x -> 5.0/2.2)

| Legacy (Do NOT use)           | New (Use in this repo)                         | Notes |
|------------------------------|-----------------------------------------------|-------|
| omni.isaac.core              | isaacsim.core.api / isaacsim.core.nodes       | Core sim/runtime access |
| omni.isaac.sensor            | isaacsim.sensors.camera / physics / rtx       | Sensor modules split by domain |
| omni.replicator.isaac        | isaacsim.replicator.writers                    | Writers, file output |
| omni.replicator.core         | isaacsim.replicator.core                       | Set up render products/annotators |
| omni.isaac.kit / utils       | isaacsim.storage.native, isaacsim.core.cloner  | Storage and cloning |
| Keyboard via omni.isaac      | carb.input (keyboard)                          | Input handled by carb.input |

Caveats:
- Keep OmniGraph Compute Mode = On Demand to avoid Physics OnSimulationStep warnings.
- Avoid mixed namespaces; prefer the isaacsim.* imports consistently.
