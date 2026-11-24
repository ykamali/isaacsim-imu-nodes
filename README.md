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

## Plotting the Allan deviation

`scripts/plot_allan.py` reads a CSV written by the node and plots the Allan deviation of the
accelerometer and gyroscope error (noisy minus true), on the same axes as the ADIS16607 datasheet
figures (x: 0.5 to 10^4 s; y: 5 to 150 ug and 0.5 to 20 deg/hr).

**Install**

    pip install -r scripts/requirements.txt

**Record a log first.** The plot script needs a CSV, and it does not create one. The node writes it:
set `stepsPerTick` to 100, set `maxSamples`, tick `logEnabled`, and press Play. The node creates
`logDir` (use an absolute path, default `/home/<user>/imu_logs`) and a file named
`imu_log_<date>_<time>.csv`. Wait for `logging done: N rows`, then press Stop and untick `logEnabled`.

**Run**

    python3 scripts/plot_allan.py                          # newest CSV in ~/imu_logs
    python3 scripts/plot_allan.py path/to/imu_log_X.csv    # a specific file
    python3 scripts/plot_allan.py path/to/imu_log_X.csv --bin 1   # full resolution (small files only)

It averages the data into 0.5 s bins (`--bin 500` at 1 kHz), reads large files in chunks, and writes
`~/log_allan_big.png` and `~/log_timeseries_big.png`.

**Reading the plot.** Solid lines are the simulation. Dashed lines are the white-noise level (N)
and dotted lines are the full model, both computed from values copied from `adis16607.yaml` into the
script. Update them in the script if the YAML changes.

**How long a record you need.** The Allan deviation can only be computed out to about a third of the
record length. To reach tau = 10^4 s you need at least 30,000 s of data, which is 30,000,000 samples
at 0.001 s. We measured about 3,585 rows/s with `stepsPerTick` = 100, so a 30M record takes about
2.3 hours and a CSV of about 5 GB. A 10-minute record (600,000 samples) reaches about 200 s.

**Use the no-gravity model for noise-only logs** (`gravity="0 0 0"`), so the true values are zero
and the log contains only the sensor error.
