import logging
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.discovery import load_platform

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_EMAIL = "email"
CONF_PASSWORD = "password"

CONFIG_SCHEMA = vol.Schema(
	{
		DOMAIN: vol.Schema({
			vol.Required(CONF_EMAIL): cv.string,
			vol.Required(CONF_PASSWORD): cv.string
		})
	},
	extra = vol.ALLOW_EXTRA
)

def setup(hass: HomeAssistant, config: ConfigType) -> bool:
	# https://community.home-assistant.io/t/new-platform-for-fan-passing-config-from-component-to-platform/136619/3
	load_platform(hass, 'climate', DOMAIN, {
		"email": config[DOMAIN][CONF_EMAIL],
		"password": config[DOMAIN][CONF_PASSWORD]
	}, config)
	return True