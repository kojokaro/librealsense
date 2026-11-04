# License: Apache 2.0. See LICENSE file in root directory.
# Copyright(c) 2026 RealSense, Inc. All Rights Reserved.

import pytest
import pyrealsense2 as rs
import logging
log = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.device_each("D555", "D585"),
    pytest.mark.device_exclude("D585S"),  # D585S selects its preset on the safety sensor
    pytest.mark.device_exclude("D585 Prototype"),
]


@pytest.fixture
def depth_mapping_sensor(test_device):
    """Yield the depth mapping sensor with its active preset restored around the test."""
    dev, _ = test_device
    sensor = dev.first_depth_mapping_sensor()
    # TODO replace with require_min_fw_version once FW publishing the control is released
    if not sensor.supports(rs.option.preset_active_index):
        pytest.skip("FW does not publish the depth mapping preset selection")
    original_index = sensor.get_option(rs.option.preset_active_index)
    yield sensor
    sensor.set_option(rs.option.preset_active_index, original_index)


def test_valid_get_set_active_index(depth_mapping_sensor):
    option_range = depth_mapping_sensor.get_option_range(rs.option.preset_active_index)
    for index in (option_range.min + 1, option_range.max, option_range.min):
        depth_mapping_sensor.set_option(rs.option.preset_active_index, index)
        assert depth_mapping_sensor.get_option(rs.option.preset_active_index) == index


def test_invalid_set_index_out_of_range(depth_mapping_sensor):
    option_range = depth_mapping_sensor.get_option_range(rs.option.preset_active_index)
    with pytest.raises(Exception):
        depth_mapping_sensor.set_option(rs.option.preset_active_index, option_range.max + 1)


@pytest.mark.parametrize("stream", [rs.stream.occupancy, rs.stream.labeled_point_cloud])
def test_set_active_index_while_streaming(depth_mapping_sensor, stream):
    profile = next(p for p in depth_mapping_sensor.profiles if p.stream_type() == stream)
    depth_mapping_sensor.open(profile)
    depth_mapping_sensor.start(lambda frame: None)
    try:
        # set_option returns only once the FW reports the new preset as active
        depth_mapping_sensor.set_option(rs.option.preset_active_index, 1)
        assert depth_mapping_sensor.get_option(rs.option.preset_active_index) == 1
    finally:
        depth_mapping_sensor.stop()
        depth_mapping_sensor.close()
