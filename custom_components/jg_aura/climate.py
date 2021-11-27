from __future__ import annotations
import asyncio

import logging

from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_HOST
from . import client
from datetime import timedelta
import async_timeout

from homeassistant.const import (
	TEMP_CELSIUS, 
	ATTR_TEMPERATURE
)
from homeassistant.components.climate.const import (
	CURRENT_HVAC_HEAT,
	CURRENT_HVAC_IDLE,
	HVAC_MODE_HEAT,
	HVAC_MODE_OFF,
	SUPPORT_TARGET_TEMPERATURE,
	SUPPORT_PRESET_MODE,
	PRESET_AWAY 
)
from homeassistant.components.climate import ClimateEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed
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
			entity.setValues(data)
			entity.async_write_ha_state()

	coordinator = DataUpdateCoordinator(
		hass,
		_LOGGER,
		# Name of the data. For logging purposes.
		name = "climate",
		update_method = async_update_data,
		# Polling interval. Will only be polled if there are subscribers.
		update_interval = timedelta(seconds = 60)
	)

	coordinator.async_add_listener(update_entities)
	
	await coordinator.async_config_entry_first_refresh()

	for thermostat in coordinator.data.thermostats:
		jgt = JGAuraThermostat(coordinator, coordinator.data.id, thermostat.id, thermostat.name, host, email, password)
		jgt.setValues(thermostat)
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

		self._hvac_list = [] # doesnt support changing mode, its always a heater or off
		self._hvac_mode = CURRENT_HVAC_IDLE
		self._support_flags = SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE
		self._preset_mode = "High"
		self._current_temp = 23

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
		return TEMP_CELSIUS

	@property
	def current_temperature(self):
		return self._current_temp

	@property
	def target_temperature(self):
		return self._target_temp

	@property
	def hvac_mode(self):
		return self._hvac_mode
	
	@property
	def hvac_action(self):
		return self._hvac_mode

	@property
	def hvac_modes(self):
		return self._hvac_list

	@property
	def preset_mode(self):
		return self._preset_mode
	@property
	def preset_modes(self):
		return ["High", "Medium", "Low", PRESET_AWAY]
	
	@property
	def supported_features(self):
		return self._support_flags

	async def async_set_temperature(self, **kwargs):
		temperature = kwargs.get(ATTR_TEMPERATURE)
		if temperature is None:
			return
		await client.setTemperatureSetPoint(self._host, self._email, self._password, self._gateway_id, self._id, temperature)
		await asyncio.sleep(5) # arbitrary wait as the above call is async beyond our control
		await self.coordinator.async_request_refresh()

	async def async_set_preset_mode(self, preset_mode):
		await client.setPreset(self._host, self._email, self._password, self._gateway_id, self._id, preset_mode)
		await asyncio.sleep(5) # arbitrary wait as the above call is async beyond our control
		await self.coordinator.async_request_refresh()

	def setValues(self, thermostat: client.Thermostat):
		self._current_temp = thermostat.tempCurrent
		self._target_temp = thermostat.tempSetPoint
		self._preset_mode = thermostat.stateName,