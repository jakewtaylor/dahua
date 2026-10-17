"""Tests for flood light model matching."""

import pytest

from custom_components.dahua import DahuaDataUpdateCoordinator


def _coordinator(model: str) -> DahuaDataUpdateCoordinator:
    coordinator = object.__new__(DahuaDataUpdateCoordinator)
    coordinator.model = model
    return coordinator


@pytest.mark.parametrize(
    "model",
    [
        "ASH26-W",
        "IPC-L26N",
        "YFL01-BLK",  # Yale floodlight, reports updateSerial IPC-L26
    ],
)
def test_flood_lights_are_flood_lights(model: str):
    assert _coordinator(model).is_flood_light()


@pytest.mark.parametrize(
    "model",
    [
        "IPC-HFW4431R-Z",
        "IPC-HDW3849HP-AS-PV",
        "DB61i",
    ],
)
def test_other_cameras_are_not_flood_lights(model: str):
    assert not _coordinator(model).is_flood_light()


def test_the_yale_flood_light_takes_the_lighting_v2_path():
    """The YFL01 has no floodlightmode config (the camera refuses
    FloodLightMode), so it must switch through Lighting_V2 like the ASH26."""
    c = _coordinator("YFL01-BLK")
    assert not c.supports_floodlightmode()
