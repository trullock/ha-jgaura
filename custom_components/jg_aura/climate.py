from __future__ import annotations
import asyncio

import logging

from homeassistant.const import UnitOfTemperature, CONF_EMAIL, CONF_PASSWORD, CONF_HOST
from . import client
from datetime import timedelta
import async_timeout

from homeassistant.const import ATTR_TEMPERATURE
from homeassistant.components.climate.const import (
    PRESET_AWAY,
    HVACAction,
    HVACMode,
    ClimateEntityFeature,
)
from homeassistant.components.climate import ClimateEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:

    host = discovery_info[CONF_HOST]
    email = discovery_info[CONF_EMAIL]
    password = discovery_info[CONF_PASSWORD]

    thermostatEntities = []

    async def async_update_data():
        # Note: asyncio.TimeoutError and aiohttp.ClientError are already
        # handled by the data update coordinator.
        async with async_timeout.timeout(10):
            return await client.loadConfig(host, email, password)

    def find_thermostat_data(id):
        for t in coordinator.data.thermostats:
            if t.id == id:
                return t
        return None

    def update_entities():
        for entity in thermostatEntities:
            data = find_thermostat_data(entity.id)
            entity.set_values(data)
            entity.async_write_ha_state()

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        # Name of the data. For logging purposes.
        name="climate",
        update_method=async_update_data,
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=timedelta(seconds=60),
    )

    coordinator.async_add_listener(update_entities)

    await coordinator.async_refresh()

    for thermostat in coordinator.data.thermostats:
        jgt = JGAuraThermostat(
            coordinator,
            coordinator.data.id,
            thermostat.id,
            thermostat.name,
            host,
            email,
            password,
        )
        jgt.set_values(thermostat)
        thermostatEntities.append(jgt)
    async_add_entities(thermostatEntities)


# https://developers.home-assistant.io/docs/core/entity/climate/
class JGAuraThermostat(CoordinatorEntity, ClimateEntity):
    def __init__(self, coordinator, gateway_id, id, name, host, email, password):
        super().__init__(coordinator)

        self._gateway_id = gateway_id
        self._id = id
        self._host = host
        self._email = email
        self._password = password

        self._attr_unique_id = "jg_aura-" + id
        self._attr_icon = "mdi:temperature-celsius"

        self._name = name

        self._attr_hvac_modes = [HVACMode.HEAT]
        self._attr_hvac_mode = HVACMode.HEAT
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
        )
        self._preset_mode = "High"
        self._attr_preset_modes = ["High", "Medium", "Low", PRESET_AWAY]

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def max_temp(self):
        return 35

    @property
    def min_temp(self):
        return 5

    @property
    def temperature_unit(self):
        return UnitOfTemperature.CELSIUS

    @property
    def preset_mode(self):
        return self._preset_mode

    async def async_set_temperature(self, **kwargs):
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        await client.setTemperatureSetPoint(
            self._host,
            self._email,
            self._password,
            self._gateway_id,
            self._id,
            temperature,
        )
        await asyncio.sleep(
            5
        )  # arbitrary wait as the above call is async beyond our control
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode):
        await client.setPreset(
            self._host,
            self._email,
            self._password,
            self._gateway_id,
            self._id,
            preset_mode,
        )
        await asyncio.sleep(
            5
        )  # arbitrary wait as the above call is async beyond our control
        await self.coordinator.async_request_refresh()

    def set_values(self, thermostat: client.Thermostat):
        self._attr_current_temperature = thermostat.tempCurrent
        self._attr_target_temperature = thermostat.tempSetPoint
        self._preset_mode = thermostat.stateName
        self._attr_hvac_action = (
            HVACAction.HEATING if thermostat.on is True else HVACAction.OFF
        )

    def set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        # no-op, UI can only set to HEAT which is the only supported mode
        pass
