#!/usr/bin/env python
# -*- coding: utf-8 -*-

#---------------------------------------------------#
#													#
#				weather_tide.py						#
#													#
#---------------------------------------------------#

"""
Version: 16/2/19

Python program for fetching weather info on openweather web server and tide info on horaire-maree web server

HISTORY:
--------
16/2/19:
- Initial program, derivated from inky_weather.py program


USAGE:
-----
From the shell: 
python weather_tide.py [-city city [countrycode]] [-h] [-v] [-tidename Name] [-weathername Name] [-tide] with:
	-h: Display help info
	-v: Verbose mode
	-tide: Include tide info 
	-tidename: Name to be used when fetching tide info
	-weathername: Name to be used when fetching weather info
	-city city [countrycode]: Name (and countrycode) to be used for title, tide and weather, unless stated otherwise for weather or tide (defaut is CITY_DEFAULT, COUNTRY_DEFAULT)

From another python program: 
get_location(): returns city, location
get_weather(city, country): returns weather_data for city, country, where weather_data = {
	'utc': time of the latest weather info in UTC,
	'time': time of the latest weather info in HH:MM,
	'temp': latest temperature for the current time,
	'condition_code': latest weather condition code for the current time,
	'condition_name': latest weather condition name for the current time
}
get_forecast(city, country, utc): returns forecast for city, country from utc, where forecast_data is an array for each day of {
	'weekday': number of the weekday of the day,
	'nameday': name of the day,
	'temp': temperature of the day at noon,
	'condition_code': weather condition code of the day at noon,
	'condition_name': weather condition name of the day at noon
}
get_tide(city): returns tide_hours, tide_coef info for the city, where tide_hours is an array of 1 or 2 hightide hours for the day, and tide_coef is the tide coef

PREREQUISITS:
------------

SIDE EFFECTS:
------------
Logs to LOG_FILENAME result (or error) of the program and displays it if verbose mode


KNOWN BUGS:
----------
- Sometimes get_location returns '' as location, and hence the forecast displayed is for CITY_DEFAULT
- TIDE_URL works only for some cities on the French West coast and returns no data if the city is not recognised (and sometimes the name should be CAPITALIZED) -- hence the option to force a city name with -tidename (list of cities here: http://www.horaire-maree.fr/)
- OPENWEATHER server works only for some cities and returns no data if the city is not recognised -- hence the option to force a city name with -weathername (list of cities is here: http://bulk.openweathermap.org/sample/city.list.json.gz)

"""


#-------------------------------------------------
#--- IMPORTS -------------------------------------
#-------------------------------------------------


from json import loads
from re import match
from time import strftime, sleep, timezone
import sys
from datetime import datetime
from requests import get
from urllib2 import Request, urlopen, URLError

#-------------------------------------------------
#--- DEFINITIONS ---------------------------------
#-------------------------------------------------

nb_forecast = 4
nb_iter = 3  # Nb d'itérations max pour essayer d'afficher les info
delay = 30  # Delai entre deux itérations

OPENWEATHER_ID = "put your id here"
OPENWEATHER_FOR = "http://api.openweathermap.org/data/2.5/forecast?q=%s&units=metric&appid=%s"
OPENWEATHER_WEA = "http://api.openweathermap.org/data/2.5/weather?q=%s&units=metric&appid=%s"
TIDE_URL = "http://www.horaire-maree.fr/maree/%s/"
LOCATION_INFO = "http://ipinfo.io"

LOG_FILENAME = "log_weather_tide.log"

HELP = "python weather_tide.py [-h][-v][-city city[countrycode]][-tidename Name][-weathername Name]\n\
with:\n\
	-h: Display help info\n\
	-v: Verbose mode\n\
	-tidename: Name to be used when fetching tide info\n\
	-weathername: Name to be used when fetching weather info\n\
	-city city [countrycode]: Name (and countrycode) to be used for tide and weather, unless stated otherwise for weather or tide (defaut is CITY_DEFAULT, COUNTRY_DEFAULT)"

weather_code_mapping = {
    "01d":	"clear sky",
    "01n":	"clear sky",
    "02d":	"few clouds",
    "02n":	"few clouds",
    "03d":	"scattered clouds",
    "03n":	"scattered clouds",
    "04d":	"broken clouds",
    "04n":	"broken clouds",
    "09d":	"shower rain",
    "09n":	"shower rain",
    "10d":	"rain",
    "10n":	"rain",
    "11d":	"thunderstorm",
    "11n":	"thunderstorm",
    "13d":	"snow",
    "13n":	"snow",
    "50d":	"mist ",
    "50n":	"mist "
}

weather_code_mapping_fr = {
	"01d": "soleil",
	"01n": "nuit claire",
	"02d": "partiellement nuageux",
	"02n": "partiellement nuageux",
    "03d":	"nuages épars",
    "03n":	"nuages épars",
    "04d":	"quelques nuages",
    "04n":	"quelques nuages",
    "09d":	"averses",
    "09n":	"averses",
    "10d":	"pluie",
    "10n":	"pluie",
    "11d":	"orage",
    "11n":	"orage",
    "13d":	"neige",
    "13n":	"neige",
    "50d":	"brouillard ",
    "50n":	"brouillard "
}

weekdays = {
	"1": "Mo",
	"2": "Tu",
	"3": "We",
	"4": "Th",
	"5": "Fr",
	"6": "Sa",
	"0": "Su"
}

weekdays_FR = {
	"1": "Lu",
	"2": "Ma",
	"3": "Me",
	"4": "Je",
	"5": "Ve",
	"6": "Sa",
	"0": "Di"
}

verbose = False

CITY_DEFAULT = "Paris"
COUNTRY_DEFAULT = "Fr"


#-------------------------------------------------
#--- FUNCTIONS -----------------------------------
#-------------------------------------------------


#-------------------------------------------------
#		Useful functions
#-------------------------------------------------


def tolog(txt):
	now = strftime('%Y/%m/%d %H:%M:%S')
	msg = "%s\t%s" % (now, txt)
	if verbose:
		print(msg)
	with open(LOG_FILENAME, 'a') as file:
		file.write(msg + "\n")
	return


def decode_arg(argv):
	"""
		Decoding of the shell arguments
	"""
	global verbose

	tolog("Decoding arguments...")
	city = ''
	country = COUNTRY_DEFAULT
	tide_city = ''
	weather_city = ''

	n = 1
	length = len(argv)
	while n < length:
		arg = argv[n]
		if arg == '-v':  # Verbose
			verbose = True
			tolog("Verbose mode")
		elif arg == '-h':  # Display help
			tolog("Help requested")
			print(HELP)
			sys.exit(0)
		elif arg == '-tidename':	# Set tide name
			tide_display = True
			if n == length:
				tolog("Error: param -tidename should be followed by a name")
			elif argv[n+1][0] == '-':
				tolog("Error: param -tidename should be followed by a name")
			else:
				tide_city = argv[n+1]
				if city == '':
					city = tide_city
				n += 1
				tolog("Set name for tide as %s" % (tide_city))
		elif arg == '-weathername':  # Set weather name
			if n == length:
				tolog("Error: param -weathername should be followed by a name")
			elif argv[n+1][0] == '-':
				tolog("Error: param -weathername should be followed by a name")
			else:
				weather_city = argv[n+1]
				n += 1
				if city == '':
					city = weather_city
				tolog("Set name for weather as %s" % (weather_city))
		elif arg == '-city':  # Set city name
			if n == length:
				tolog("Error: param -city should be followed by a name")
			elif argv[n+1][0] == '-':
				tolog("Error: param -city should be followed by a name")
			else:
				n += 1
				city = argv[n]
				tolog("Set city name as %s" % (city))
				if n+1 < length:
					if not argv[n+1][0] == '-':
						n += 1
						country = argv[n]
						tolog("Set country name as %s" % (country))
		elif arg[0] == '-':
			tolog("Errorenous option: %s" %(arg))
		n += 1
	return city, country, tide_city, weather_city


#-------------------------------------------------
#		Location function
#-------------------------------------------------

#---- Fetch location

def get_location():
	"""
		Fetches location information and returns city, country
	"""
	city = ''
	country = ''

	tolog("Fetching location info...")
	try:
		res = get(LOCATION_INFO)
		result = res.status_code
		if (result == 200):
			json_data = loads(res.text)
			city = json_data["city"]
			country = json_data["country"]
			tolog("...found city = %s, country = %s" %(city, country))
		else:
			tolog("...error fetching location info: request returned status %s" % (result))
	except Exception as e:
		tolog("...error fetching location info: %s" % (e))

	return city, country


#-------------------------------------------------
#		Weather functions
#-------------------------------------------------

#---- Fetch weather info

def fetch_weather(url):
	"""
		Fetches weather info on openweather site and returns JSON response
	"""
	tolog("Fetching weather info with url %s..." %(url))
	try:
		response = get(url).text
		weather_json = loads(response)
		tolog("...fetching OK")
		return weather_json
	except Exception as e:
		tolog("...error fetching weather info: %s" %(e))
		return {}


def get_weather(city, country):
	"""
		Fetches current weather info and returns UTC and time of the weather, temperature, name and code of the weather condition
	"""

	weather_data = {}

	location_string = city + ',' + country

 	#----- Extract current weather data

	tolog("Fetching current weather...")

	weather_current = fetch_weather(OPENWEATHER_WEA %(location_string, OPENWEATHER_ID))
	if weather_current == {}:
		tolog("...error reading weather info: cannot read current weather")
	else:
		try:
			temp_current = weather_current["main"]["temp"]
			tolog("...temperature %s" %(temp_current))

			utc = int(weather_current["dt"])
			time_current = datetime.utcfromtimestamp(utc-timezone).strftime('%H:%M')
			tolog("...hour %s" % (time_current))

			code_current = weather_current["weather"][0]["icon"]
			if code_current in weather_code_mapping:
				if country == 'Fr':
					weather_current = weather_code_mapping_fr[code_current]
				else:
					weather_current = weather_code_mapping[code_current]
			else:
				weather_current = '?'
			tolog("...current weather is %s (code %s)" %(weather_current, code_current))
			weather_data = {
				'utc': utc,
				'time': time_current,
				'temp': temp_current,
				'condition_code': code_current,
				'condition_name': weather_current
			}

		except Exception as e:
			tolog("...error reading current weather: %s" % (e))

	return weather_data


def get_forecast(city, country, utc):
	"""
		Fetches forecast weather info for city, country, for the days foloowing UTC
	"""
	forecast_data = {}

	#----- Extract weather forecast data

	weather_forecast = fetch_weather(OPENWEATHER_FOR % (city + ',' + country, OPENWEATHER_ID))
	if weather_forecast == {}:
		tolog("...error reading weather info: cannot read forecast weather")
	else:
		try:
			forecast_list = weather_forecast["list"]

			utc12 = (utc / 86400) * 86400 + 43200	# UTC for the day at Noon

			for day in range(nb_forecast):
				forecast_data[day] = {
					'weekday': '',
					'nameday': '?',
					'temp': '?',
					'condition_code': '?',
					'condition_name': '?'
				}
				utc12 += 86400

				wd = datetime.utcfromtimestamp(utc12).strftime('%w')
				if wd in weekdays:
					if (country == 'Fr'):
						wd_name = weekdays_FR[wd]
					else:
						wd_name = weekdays[wd]
				else:
					wd_name = '?'
				forecast_data[day]["nameday"] = wd_name
				forecast_data[day]['weekday'] = wd
				tolog("Fetching forecast weather for %s (%s)..." % (wd_name, wd))

				for i in range (len(forecast_list)):
					if int(forecast_list[i]["dt"]) == utc12:
						temp = forecast_list[i]["main"]["temp"]
						code = forecast_list[i]["weather"][0]["icon"]
						if code in weather_code_mapping:
							if country == 'Fr':
								weather_name = weather_code_mapping_fr[code]
							else:
								weather_name = weather_code_mapping[code]
						else:
							weather_name = '?'
						forecast_data[day]['temp'] = temp
						forecast_data[day]['condition_code'] = code
						forecast_data[day]['condition_name'] = weather_name
						tolog("...temperature %s, weather %s (code %s)" % (temp, weather_name, code))
						break

		except Exception as e:
			tolog("...error reading forecast weather: %s" %(e))
	return forecast_data


#-------------------------------------------------
#		Tide functions
#-------------------------------------------------

#---- Fetch tide info

def extract_text(line, st1, st2, pos0):
	pos1 = line.find(st1, pos0)
	if pos1 == -1:
		return '', -1
	pos2 = line.find(st2, pos1 + len(st1))
	if pos2 == -1:
		return '', -1
	text = line[pos1 + len(st1):pos2]
	return (text, pos2)


def get_tide(city):

	tide_hours = []
	tide_coef = ''

	tolog("Fetching tide info...")
	try:
		req = Request(TIDE_URL % (city))
		response_url = urlopen(req)
	except URLError as e:
		if hasattr(e, 'reason'):  # One reason (unsure what!)
			error = e.reason
		elif hasattr(e, 'code'):  # Another reason (unsure what!)
			error = e.code
		tolog("Error accessing tide server: %s" % (error))
		return ([], '')

	try:
		response = response_url.read()
		pos = response.find("i_donnesJour", 0)
		if pos == -1:
			raise ValueError("No tag '%s' found in tide site" % ("i_donnesJour"))
		pos = response.find("bluesoftoffice", pos+1)
		if pos == -1:
			raise ValueError("No 1st tag '%s' found in tide site" % ("bluesoftoffice"))
		pos = response.find("bluesoftoffice", pos+1)
		if pos == -1:
			raise ValueError("No 2nd tag '%s' found in tide site" % ("bluesoftoffice"))

		coef_text, pos = extract_text(response, "<strong>", "</strong><", pos)
		if pos == -1:
			raise ValueError("No tag '%s' found in tide site" % ("<strong>"))
		if not match(r"[0-9]+$", coef_text):
			raise ValueError("Incoherent tide coef: %s" % (coef_text))

		tide_coef = coef_text
		tolog("Tide coef found: %s" % (tide_coef))

		tide_text, pos = extract_text(response, "<strong>", "</strong><", pos+1)
		if pos == -1:
			raise ValueError("No 1st tag '%s' for PM1 found in tide site" % ("<strong>"))
		tide_text, pos = extract_text(response, "<strong>", "</strong><", pos+1)
		if pos == -1:
			raise ValueError("No 2nd tag '%s' pour PM1 found in tide site" % ("<strong>"))
		if not match(r"[0-9][0-9]h[0-9][0-9]$", tide_text):
			raise ValueError("PM1 hour incoherent: %s" % (tide_text))

		tide_hours.append(tide_text.replace('h', ':'))
		tolog("PM1 found: %s" % (tide_text))

		tide_text, pos = extract_text(response, "<strong>", "</strong><", pos+1)
		if pos == -1:
			tolog("No 1st tag '%s' for PM2 found in tide site" % ("<strong>"))
			tide_hours.append('')
			return tide_hours, tide_coef
		tide_text, pos = extract_text(response, "<strong>", "</strong><", pos+1)
		if pos == -1:
			tolog("No 2nd tag '%s' for PM2 found in tide site" % ("<strong>"))
			tide_hours.append('')
			return tide_hours, tide_coef
		if not match(r"[0-9][0-9]h[0-9][0-9]$", tide_text):
			tolog("PM2 hour incoherent: %s" % (coef_text))
			tide_hours.append('')
			return tide_hours, tide_coef
		tide_hours.append(tide_text.replace('h', ':'))
		tolog("PM2 found: %s" % (tide_text))

		return tide_hours, tide_coef
	except ValueError as e:
		tolog(e)
	return ([], '?')


#-------------------------------------------------
#		Main function for shell command
#-------------------------------------------------

if __name__ == "__main__":

	tolog("==== Fetching of weather and tide info")

	city, country, tide_city, weather_city = decode_arg(sys.argv)

	if city == "":
		for i in range(nb_iter):
			city, country = get_location()
			if city != "":
				break
			sleep(delay)
	
	if city == "":
		tolog("Too many attemps to fetch location info, I settle for %s, %s" %
			(CITY_DEFAULT, COUNTRY_DEFAULT))
		city = CITY_DEFAULT
		country = COUNTRY_DEFAULT
	else:
		print("=== Tide and weather info for %s (%s) ===" %(city, country))
	
	if tide_city == '':
		tide_city = city
	
	tolog("Fetching tide info for %s" %(tide_city))
	for i in range(nb_iter):
		tide_hours, tide_coef = get_tide(tide_city)		
		if tide_coef != '':
			break
		sleep(delay)

	if tide_coef == '':
		tolog("Too many attemps to fetch tide info, I give up!")
	elif tide_coef == '?':
		tolog("Cannot fetch tide info for %s" % (tide_city))
	else:
		print("\nTide info for %s" % (tide_city))
		print("Tide coefficient: %s" %(tide_coef))
		if len(tide_hours) == 1:
			print("Hightide time: %s" %(tide_hours[0]))
		elif len(tide_hours) == 2:
			print("First hightide time: %s" %(tide_hours[0]))
			print("Second hightide time: %s" % (tide_hours[1]))

	if weather_city == '':
		weather_city = city

	tolog("Fetching weather info for %s (%s)" % (weather_city, country))
	for i in range(nb_iter):
		weather_data = get_weather(weather_city, country)
		if weather_data != {}:
			break
		sleep(delay)

	if weather_data == {}:
		tolog("Too many attemps to fetch weather info, I give up!")
	else:
		print("\nWeather info for %s (%s)" % (weather_city, country))
		print("Weather time: %s" % (weather_data['time']))
		print("Temperature: %s" % (weather_data['temp']))
		print("Weather condition: %s (code %s)" %(weather_data['condition_name'], weather_data['condition_code']))

		tolog("Fetching forecast info for %s (%s)" % (weather_city, country))
		for i in range(nb_iter):
			forecast_data = get_forecast(weather_city, country, weather_data['utc'])
			if forecast_data != {}:
				break
			sleep(delay)

		if forecast_data == {}:
			tolog("Too many attemps to fetch forecast info, I give up!")
		else:
			print("\nForecast info for %s (%s)" % (weather_city, country))
			for day in range(nb_forecast):
				daily_forecast = forecast_data[day]
				print("For %s at Noon: Weather is %s, temperature is %s" % (
					daily_forecast['nameday'],
					daily_forecast['condition_name'],
					daily_forecast['temp'])
				)

#-------------------------------------------------
#----- END OF THE PROGRAMME ----------------------
#-------------------------------------------------
