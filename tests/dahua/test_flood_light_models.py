"""Tests for flood light model matching, and the Yale YFL01's coaxial path."""

from types import SimpleNamespace

import pytest

from custom_components.dahua import DahuaDataUpdateCoordinator
from custom_components.dahua.client import SECURITY_LIGHT_TYPE
from custom_components.dahua.light import FloodLight


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


def test_only_the_yale_flood_light_switches_through_coaxial():
    """The ASH26 keeps its Lighting_V2 path; nothing measured says it should move."""
    assert _coordinator("YFL01-BLK").flood_light_uses_coaxial()
    assert not _coordinator("YFL01-BLK").supports_floodlightmode()
    assert not _coordinator("ASH26-W").flood_light_uses_coaxial()
    assert not _coordinator("IPC-L26N").flood_light_uses_coaxial()


@pytest.mark.parametrize("white_light,on", [("On", True), ("Off", False)])
def test_the_yale_flood_light_reads_white_light(white_light: str, on: bool):
    """Lighting_V2 says Off while the lamp is lit, so it must not be what is read."""
    c = _coordinator("YFL01-BLK")
    c._supports_floodlightmode = False
    c._channel = 0
    c.data = {
        "status.status.WhiteLight": white_light,
        "table.Lighting_V2[0][0][1].Mode": "Off",
    }
    c.get_status_value = lambda key: c.data.get(f"status.status.{key}", "")
    c.get_profile_mode = lambda: "0"
    assert c.is_flood_light_on() is on


def test_the_yale_flood_light_has_no_second_security_light():
    """coaxial Type=1 is the flood light itself on this camera."""
    c = _coordinator("YFL01-BLK")
    c.supports_security_light = lambda: True
    c.uses_recorder_deterrence = lambda: False
    assert not c.creates_security_light_entity()


class _Client:
    def __init__(self):
        self.coaxial = []
        self.other = []

    async def async_set_coaxial_control_state(self, channel, dahua_type, enabled):
        self.coaxial.append((channel, dahua_type, enabled))

    async def async_get_floodlightmode(self):
        self.other.append("get_floodlightmode")

    async def async_set_floodlightmode(self, mode):
        self.other.append("set_floodlightmode")

    async def async_set_lighting_v2_for_flood_lights(self, *args):
        self.other.append("lighting_v2")


async def _refresh():
    return None


def _yale_flood_light():
    coordinator = SimpleNamespace(
        client=_Client(),
        _supports_floodlightmode=False,
        _floodlight_mode=None,
        flood_light_uses_coaxial=lambda: True,
        get_channel=lambda: 0,
        get_channel_number=lambda: 1,
        get_profile_mode=lambda: "0",
        is_nvr_channel=lambda: False,
        async_refresh=_refresh,
    )
    entity = object.__new__(FloodLight)
    entity._coordinator = coordinator
    return entity, coordinator.client


async def test_the_yale_flood_light_switches_on_and_off_through_coaxial():
    """Channel 1 is what was measured; the camera refuses FloodLightMode outright."""
    entity, client = _yale_flood_light()

    await entity.async_turn_on()
    await entity.async_turn_off()

    assert client.coaxial == [
        (1, SECURITY_LIGHT_TYPE, True),
        (1, SECURITY_LIGHT_TYPE, False),
    ]
    assert client.other == [], "no FloodLightMode or Lighting_V2 writes"
