#
#    @@@@@@@@@@@@@@@@@@@@
#    @@@@@@@@@&@@@&&@@@@@
#    @@@@@ @@  @@    @@@@
#    @@@@@ @@  @@    @@@@
#    @@@@@ @@  @@    @@@@ Copyright (c) 2023, Acceleration Robotics®
#    @@@@@ @@  @@    @@@@ Author: Víctor Mayoral Vilches <victor@accelerationrobotics.com>
#    @@@@@ @@  @@    @@@@ Author: Alejandra Martínez Fariña <alex@accelerationrobotics.com>
#    @@@@@@@@@&@@@@@@@@@@
#    @@@@@@@@@@@@@@@@@@@@
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode
from tracetools_launch.action import Trace
from tracetools_trace.tools.names import DEFAULT_EVENTS_ROS
from tracetools_trace.tools.names import DEFAULT_EVENTS_KERNEL
from tracetools_trace.tools.names import DEFAULT_CONTEXT

 
def generate_launch_description():
     # Trace
    trace = Trace(
        session_name="a1_perception_nodes_fpga",
        events_ust=[
            "robotperf_benchmarks:*",
            "robotcore_power:*",
            "ros2_image_pipeline:*",
            "ros2:*"
        ]
        + DEFAULT_EVENTS_ROS,
        context_fields={
                'kernel': [],
                'userspace': ['vpid', 'vtid', 'procname'],
        },
        # events_kernel=DEFAULT_EVENTS_KERNEL,
    )

    power_container = ComposableNodeContainer(
        name="power_container",
        namespace="robotcore/power",
        package="rclcpp_components",
        executable="component_container",
        composable_node_descriptions=[
            ComposableNode(
                package="robotcore-power",
                namespace="robotcore/power",
                plugin="robotcore::power::PowerComponent",
                name="power_component",
                parameters=[
                    {"publish_rate": 20.0},
                    {"power_lib": "rapl"}
                ],
            ),
            
        ],
        output="screen",
    )
 
    perception_container = ComposableNodeContainer(
        name="perception_container",
        namespace="",
        package="rclcpp_components",
        executable="component_container",
        composable_node_descriptions=[
            ComposableNode(
                package="a1_perception_2nodes",
                plugin="robotperf::perception::ImageInputComponent",
                namespace="robotperf",
                name="image_input_component",
                remappings=[
                    ("image", "/camera/image_raw"),
                    ("camera_info", "/camera/camera_info"),
                ],
                extra_arguments=[{'use_intra_process_comms': True}],
            ),
            ComposableNode(
                namespace="robotperf/benchmark",
                package="image_proc",
                plugin="image_proc::RectifyNodeFPGA",
                name="rectify_node_fpga",
                remappings=[
                    ("image", "/robotperf/input"),
                    ("camera_info", "/camera/camera_info"),
                    ("image_rect", "/robotperf/benchmark/image_rect"),
                ],
                extra_arguments=[{'use_intra_process_comms': True}],
            ),
            ComposableNode(
                namespace="robotperf/benchmark",
                package="image_proc",
                plugin="image_proc::ResizeNodeFPGA",
                name="resize_node_fpga",
                remappings=[
                    ("camera_info", "/camera/camera_info"),
                    ("image", "/robotperf/benchmark/image_rect"),
                    ("resize", "/robotperf/benchmark/resize"),
                ],
                parameters=[
                    {
                        "scale_height": 2.0,
                        "scale_width": 2.0,
                    }
                ],
                extra_arguments=[{'use_intra_process_comms': True}],
            ),
            ComposableNode(
                package="a1_perception_2nodes",
                plugin="robotperf::perception::ImageOutputComponent",
                name="image_output_component",
                namespace="robotperf",
                remappings=[
                    ("image", "/robotperf/benchmark/resize"),
                    ("camera_info", "/camera/camera_info"),
                ],
                extra_arguments=[{'use_intra_process_comms': True}],
            ),
        ],
        output="screen",
    )

    return LaunchDescription([
        # LTTng tracing
        trace,
        # image pipeline
        perception_container,
        power_container
    ])