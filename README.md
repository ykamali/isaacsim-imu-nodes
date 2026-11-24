# MuJoCo IMU Noise: an OmniGraph node for Isaac Sim 6.2

An Action Graph node, **MuJoCo IMU Noise**, that steps a MuJoCo model using a compiled
IMU noise plugin (`imu_nbk_plugin.so`) and outputs noisy accelerometer and gyroscope readings.
The plugin comes from https://github.com/jay1871/imu-standalone.

## Requirements
- Isaac Sim 6.2 built from source (ships MuJoCo 3.12.0 for Python)
- The plugin built against **MuJoCo 3.12.0** (a plugin built for one MuJoCo version should not be loaded by another). Recheck the version when moving to Isaac Sim 6.3.

## Install
1. Build the plugin (see the imu-standalone README).
2. Copy `isaacsim.imu.nodes/` into `<isaacsim>/source/extensions/` and run `./build.sh`.
3. In Isaac Sim: Window > Extensions, enable `isaacsim.imu.nodes`.
4. In an Action Graph, add **On Playback Tick** and **MuJoCo IMU Noise** (category: Isaacsim) and connect Tick to Exec In.

## Inputs
| Input | Default | Notes |
|---|---|---|
| `pluginPath` | `/home/yasmin/imu-standalone/build/mujoco_plugin/imu_nbk_plugin.so` | Set to your own path |
| `modelPath` | `/home/yasmin/imu-standalone/models/free_body_imu_nograv.xml` | Use an absolute `config_path` inside the XML |
| `logEnabled` | off | Tick before Play to write a CSV with one row per MuJoCo step |
| `logDir` | `/home/yasmin/imu_logs` | |
| `maxSamples` | 10000 | Stop logging after this many steps |
| `stepsPerTick` | 1 | Use 100 for long records |

## Notes
- The default model has gravity switched off, so outputs are pure sensor noise. Use a model with gravity to read about 9.8 m/s2 on Z once the box has landed.
- The plugin runs on its **own MuJoCo body**. It does not read objects in the Isaac Sim scene.
- Stop then Play does not reset the plugin. Restart Isaac Sim for a clean run.
- Units: m/s2 and rad/s (from the plugin's config).
