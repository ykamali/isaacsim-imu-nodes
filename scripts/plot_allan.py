# plot_log.py -- Allan deviation from the CSV written by the MuJoCo IMU Noise node
# usage: python3 ~/plot_log.py [file.csv] [--bin N]
#   default file : newest in ~/imu_logs
#   --bin N      : rows averaged per bin. Default 500 (= 0.5 s at 1 kHz).
#                  --bin 1 keeps full resolution (small files only, uses a lot of memory).
import sys, glob, os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

G = 9.797464   # m/s^2 per g (same constant as the YAML)

# ---- values copied from config/adis16607.yaml (SI units) ----
acc = dict(
    N=[7.2625e-04, 7.0562e-04, 6.7700e-04],
    K=[5.5124e-06, 5.4944e-06, 5.7125e-06],
    S=[[5.4098e-05, 5.8207e-05, 1.2322e-04], [5.2901e-05, 5.4878e-05, 9.2599e-05], [1.0152e-04, 1.0658e-04, 1.5937e-04]],
    T=[[20.33, 250.43, 4305.93], [21.63, 205.52, 2165.97], [14.77, 130.93, 1904.57]])
gyro = dict(
    N=[5.1501e-05, 4.7935e-05, 2.1821e-05],
    K=[1.2358e-07, 2.1677e-07, 1.0478e-07],
    S=[[5.5083e-06, 5.1217e-06, 4.9446e-06], [8.5087e-06, 8.2528e-06, 1.0141e-05], [4.6124e-06, 4.5869e-06, 5.6792e-06]],
    T=[[23.80, 196.13, 1576.73], [17.16, 165.12, 1339.84], [13.22, 134.12, 1532.73]])

# ---- model prediction (assumes each S entry is the stationary std of its Gauss-Markov pole
#      and that the terms add as variances; check against the plugin if the curve is offset) ----
def gm_avar(sig, T, tau):
    x = np.asarray(tau, float) / T
    exact = (2 * sig**2 / x**2) * (x + 2*np.exp(-x) - 0.5*np.exp(-2*x) - 1.5)
    series = 2 * sig**2 * (x/3 - x**2/4)          # small-x expansion avoids cancellation
    return np.where(x < 1e-3, series, exact)

def model_adev(N, K, sigs, Ts, tau):
    tau = np.asarray(tau, float)
    v = N**2 / tau + K**2 * tau / 3
    for s, T in zip(sigs, Ts):
        v = v + gm_avar(s, T, tau)
    return np.sqrt(v)

# ---- arguments ----
args = sys.argv[1:]
BIN = 500
if "--bin" in args:
    i = args.index("--bin")
    BIN = int(args[i + 1])
    del args[i:i + 2]
args = args or ["~/imu_logs/imu_log_*.csv"]
files = sorted(f for a in args for f in glob.glob(os.path.expanduser(a)))
if not files:
    sys.exit("No CSV files found. Check ~/imu_logs.")
path = files[-1]
print("file:", path)

# ---- read in chunks and average into bins ----
cols = ["time_s", "acc_err_x", "acc_err_y", "acc_err_z",
        "gyro_err_x", "gyro_err_y", "gyro_err_z"]
means, carry, tau0, n_rows = [], np.empty((0, 6)), None, 0
for chunk in pd.read_csv(path, comment="#", usecols=cols, chunksize=5_000_000):
    if tau0 is None:
        tau0 = float(np.median(np.diff(chunk["time_s"].values[:2000])))
    arr = np.vstack([carry, chunk[cols[1:]].values])
    n_rows += len(chunk)
    nb = len(arr) // BIN
    means.append(arr[:nb * BIN].reshape(nb, BIN, 6).mean(axis=1))
    carry = arr[nb * BIN:]
means = np.vstack(means)
TAU = BIN * tau0
print(f"rows: {n_rows} | tau0: {tau0:.6g} s | record: {n_rows * tau0:.0f} s "
      f"({n_rows * tau0 / 3600:.2f} h) | bin: {TAU:g} s | bins: {len(means)}")

# ---- overlapping Allan deviation on the bin means ----
def oadev(x):
    n = len(x)
    theta = np.concatenate(([0.0], np.cumsum(x) * TAU))
    ms = np.unique(np.round(np.logspace(0, np.log10(max(n // 3, 2)), 60)).astype(int))
    taus, devs = [], []
    for m in ms:
        dd = theta[2*m:] - 2*theta[m:-m] + theta[:-2*m]
        taus.append(m * TAU)
        devs.append(np.sqrt(np.sum(dd * dd) / (2 * (m * TAU) ** 2 * dd.size)))
    return np.array(taus), np.array(devs)

to_ug = lambda x: x / (G * 1e-6)
to_dph = lambda x: x * (180 / np.pi) * 3600
colors = ["#a01040", "#007060", "#10a0e0"]
names = ["accX", "accY", "accZ", "gyroX", "gyroY", "gyroZ"]

# ---- Figure 1: Allan deviation ----
fig, ax = plt.subplots(1, 2, figsize=(13, 5.5))
for k in range(6):
    tau, dev = oadev(means[:, k])
    conv = to_ug if k < 3 else to_dph
    p = acc if k < 3 else gyro
    i = k % 3
    a = ax[0 if k < 3 else 1]
    a.loglog(tau, conv(dev), color=colors[i], label="XYZ"[i])                          # simulation
    a.loglog(tau, conv(p["N"][i] / np.sqrt(tau)), "--", color=colors[i], alpha=0.4)   # white noise only
    a.loglog(tau, conv(model_adev(p["N"][i], p["K"][i], p["S"][i], p["T"][i], tau)),
             ":", color=colors[i], lw=2, alpha=0.9)                                    # full model
    if tau[0] <= 1.0 <= tau[-1]:
        print(f"{names[k]}: Allan deviation at tau=1 s: {np.interp(1.0, tau, dev):.3e} (SI units)")
ax[0].set_title("Accelerometer"); ax[0].set_ylabel("Allan deviation (ug)")
ax[1].set_title("Gyroscope");     ax[1].set_ylabel("Allan deviation (deg/hr)")
for a in ax:
    a.set_xlabel("Integration time (s)")
    a.set_xlim(0.5, 1e4)
    a.grid(True, which="both")
    a.legend()
ax[0].set_ylim(5, 150)
ax[1].set_ylim(0.5, 20)
fig.suptitle("solid: simulation   dashed: white noise (N)   dotted: full model from YAML", fontsize=10)
fig.savefig(os.path.expanduser("~/log_allan_big.png"), dpi=150)

# ---- Figure 2: error signal (bin means) ----
t = (np.arange(len(means)) + 0.5) * TAU
fig2, a2 = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
for k, lab in enumerate("XYZ"):
    a2[0].plot(t, means[:, k], lw=0.5, label=lab)
    a2[1].plot(t, means[:, 3 + k], lw=0.5, label=lab)
a2[0].set_ylabel("accel error, bin mean (m/s^2)")
a2[1].set_ylabel("gyro error, bin mean (rad/s)")
a2[1].set_xlabel("time (s)")
for a in a2:
    a.legend()
    a.grid(True)
fig2.savefig(os.path.expanduser("~/log_timeseries_big.png"), dpi=150)
print("saved: ~/log_allan_big.png and ~/log_timeseries_big.png")

