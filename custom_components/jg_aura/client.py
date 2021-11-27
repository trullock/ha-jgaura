
import aiohttp
import urllib

import logging
_LOGGER = logging.getLogger(__name__)

async def loadConfig(host, email, password):
	async with aiohttp.ClientSession() as session:

		url = 'https://' + host + '/getDevices?email=' + urllib.parse.quote(email) + '&password=' + urllib.parse.quote(password)
		async with session.get(url) as resp:
			json = await resp.json()
			gateway = parseJson(json)
			return gateway

async def setPreset(host, email, password, gatewayId, deviceId, stateName):
	async with aiohttp.ClientSession() as session:
		url = 'https://' + host + '/setDeviceState?email=' + urllib.parse.quote(email) + '&password=' + urllib.parse.quote(password) + '&gatewayId=' + urllib.parse.quote(str(gatewayId)) + '&deviceId=' + urllib.parse.quote(str(deviceId)) + '&stateName=' + urllib.parse.quote(stateName)
		async with session.get(url) as resp:
			text = await resp.text()
			#_LOGGER.warn(text)
			return resp.status == 200

async def setTemperatureSetPoint(host, email, password, gatewayId, deviceId, temperature):
	async with aiohttp.ClientSession() as session:
		url = 'https://' + host + '/setTemperatureSetPoint?email=' + urllib.parse.quote(email) + '&password=' + urllib.parse.quote(password) + '&gatewayId=' + urllib.parse.quote(str(gatewayId)) + '&deviceId=' + urllib.parse.quote(str(deviceId)) + '&temp=' + urllib.parse.quote(str(temperature))
		async with session.get(url) as resp:
			text = await resp.text()
			#_LOGGER.warn(text)
			return resp.status == 200

def parseJson(json):
	thermostats = []
	for thermostat in json['thermostats']:
		thermostats.append(Thermostat(thermostat['id'], thermostat['name'], thermostat['on'], thermostat['state']['name'], thermostat['state']['auto'], thermostat['state']['away'], thermostat['state']['party'], thermostat['temperatureCurrent'], thermostat['temperatureSetPoint']))
	gateway = Gateway(json['id'], json['name'], thermostats)
	return gateway



class Gateway():
	def __init__(self, id, name, thermostats):
		self._id = id
		self._name = name
		self._thermostats = thermostats

	@property
	def id(self):
		return self._id

	@property
	def name(self):
		return self._name

	@property
	def thermostats(self):
		return self._thermostats

class Thermostat():
	def __init__(self, id, name, on, stateName, auto, away, party, tempCurrent, tempSetPoint):
		self._id = id
		self._name = name
		self._on = on
		self._stateName = stateName
		self._auto = auto
		self._away = away
		self._party = party
		self._tempCurrent = tempCurrent
		self._tempSetPoint = tempSetPoint

	@property
	def id(self):
		return self._id

	@property
	def name(self):
		return self._name

	@property
	def on(self):
		return self._on
	@property
	def stateName(self):
		return self._stateName

	@property
	def auto(self):
		return self._auto

	@property
	def away(self):
		return self._away
	@property
	def party(self):
		return self._party

	@property
	def tempCurrent(self):
		return self._tempCurrent

	@property
	def tempSetPoint(self):
		return self._tempSetPoint



#async def main():
#	await loadConfig()

#asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
#asyncio.run(main())