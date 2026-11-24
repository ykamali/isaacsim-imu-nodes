// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <isaacsim/imu/nodes/IExampleNodes.hpp>

#include <carb/BindingsPythonUtils.h>

CARB_BINDINGS("isaacsim.imu.nodes.python")

PYBIND11_MODULE(_isaacsim_imu_nodes, m)
{
    using namespace isaacsim::imu::nodes;

    m.doc() = "Python bindings for isaacsim.imu.nodes";

    carb::defineInterfaceClass<IExampleNodes>(
        m, "IExampleNodes", "acquire_example_nodes_interface", "release_example_nodes_interface");
}
