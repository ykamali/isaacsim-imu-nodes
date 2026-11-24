# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import os
import time

import mujoco
import omni.graph.core as og

EXPECTED_MUJOCO = "3.12.0"

_plugin_loaded_path = None
_loaded_model_path = None
_model = None
_data = None

_log_fh = None
_log_count = 0
_log_done = False


class OgnExamplePython:
    """Steps the MuJoCo IMU plugin, outputs the noisy readings, optionally logs every step."""

    @staticmethod
    def compute(db) -> bool:
        global _plugin_loaded_path, _loaded_model_path, _model, _data
        global _log_fh, _log_count, _log_done

        if mujoco.__version__ != EXPECTED_MUJOCO:
            db.log_error(
                f"Plugin built for MuJoCo {EXPECTED_MUJOCO}, Isaac Sim has "
                f"{mujoco.__version__}. Rebuild the plugin."
            )
            return False

        plugin_path = db.inputs.pluginPath
        model_path = db.inputs.modelPath

        try:
            if _plugin_loaded_path != plugin_path:
                mujoco.mj_loadPluginLibrary(plugin_path)
                _plugin_loaded_path = plugin_path
            if _model is None or _loaded_model_path != model_path:
                _model = mujoco.MjModel.from_xml_path(model_path)
                _data = mujoco.MjData(_model)
                _loaded_model_path = model_path
        except Exception as exc:
            db.log_error(f"MuJoCo load failed: {exc}")
            return False

        if _model.nsensordata < 12:
            db.log_error(f"Expected at least 12 sensor values, got {_model.nsensordata}.")
            return False

        # open the log file when logging is switched on
        if db.inputs.logEnabled:
            if _log_fh is None and not _log_done:
                os.makedirs(db.inputs.logDir, exist_ok=True)
                fname = os.path.join(db.inputs.logDir, time.strftime("imu_log_%Y%m%d_%H%M%S.csv"))
                _log_fh = open(fname, "w")
                _log_fh.write(f"# timestep_s={_model.opt.timestep}, model={model_path}\n")
                _log_fh.write(
                    "step,time_s,"
                    "acc_true_x,acc_true_y,acc_true_z,gyro_true_x,gyro_true_y,gyro_true_z,"
                    "acc_noisy_x,acc_noisy_y,acc_noisy_z,gyro_noisy_x,gyro_noisy_y,gyro_noisy_z,"
                    "acc_err_x,acc_err_y,acc_err_z,gyro_err_x,gyro_err_y,gyro_err_z\n"
                )
                _log_count = 0
                print(f"[MuJoCo IMU Noise] logging to {fname}")
        else:
            if _log_fh is not None:
                _log_fh.close()
                _log_fh = None
            _log_done = False

        s = None
        for _ in range(max(1, int(db.inputs.stepsPerTick))):
            mujoco.mj_step(_model, _data)
            s = [float(x) for x in _data.sensordata[:12]]  # 0-5 true, 6-11 noisy (acc then gyro)

            if _log_fh is not None:
                err = [s[6 + k] - s[k] for k in range(6)]
                row = [_log_count, _data.time] + s + err
                _log_fh.write(",".join(f"{v:.9g}" for v in row) + "\n")
                _log_count += 1
                if _log_count % 10000 == 0:
                    _log_fh.flush()
                if _log_count >= db.inputs.maxSamples:
                    _log_fh.close()
                    _log_fh = None
                    _log_done = True
                    print(f"[MuJoCo IMU Noise] logging done: {_log_count} rows")

        db.outputs.accNoisy = s[6:9]
        db.outputs.gyroNoisy = s[9:12]
        db.outputs.execOut = og.ExecutionAttributeState.ENABLED
        return True
