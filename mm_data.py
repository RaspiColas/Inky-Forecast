#!/usr/bin/env python
# -*- coding: utf-8 -*-

#---------------------------------------------------#
#													#
#				mm_data.py							#
#				by N.Mercouroff						#
#													#
#---------------------------------------------------#

version_prog = "200720"
name_prog = "mm_data.py"

"""
Version: 20/7/20

Python program for fetching weather info on openweather web server and tide info on horaire-maree web server

HISTORY:
--------
19/7/20:
- Added config file
- Cleanup of the code
- Changed process to fetch global IP address

18/2/19:
- Added -tide option to shell command to force display of tide information

16/2/19:
- Initial program, derivated from inky_weather.py program


USAGE:
-----
From the shell: 
python mm_data.py [-city city [countrycode]] [-h] [-v] [-tidename Name] [-weathername Name] [-tide] with:
	-h: Display help info
	-v: Verbose mode
	-tide: Include tide info 
	-tidename: Name to be used when fetching tide info
	-weathername: Name to be used when fetching weather info
	-city city [countrycode]: Name (and countrycode) to be used for title, tide and weather, unless stated otherwise for weather or tide (defaut is city_default, country_default)

From another python program: 
get_location(): returns city, location
get_weather(city, country, openweather_ID): returns weather_data for city, country, where weather_data = {
	'utc': time of the latest weather info in UTC,
	'time': time of the latest weather info in HH:MM,
	'temp': latest temperature for the current time,
	'condition_code': latest weather condition code for the current time,
	'condition_name': latest weather condition name for the current time
}
get_forecast(city, country, openweather_ID): returns forecast for city, country, where forecast_data is an array for each day of {
	'weekday': number of the weekday of the day,
	'nameday': name of the day,
	'temp': temperature of the day at noon,
	'condition_code': weather condition code of the day at noon,
	'condition_name': weather condition name of the day at noon
}
get_tide(city): returns tide_hours, tide_coef info for the city, where tide_hours is an array of 1 or 2 hightide hours for the day, and tide_coef is the tide coef


PREREQUISITS:
------------
Requires the following file:
- config_magicmirror.conf : configuration data
- token.pickle : to store the user's access and refresh tokens (regenerated)


Installation of the libs:
	pip install geopy
	pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
	pip install ConfigParser

SIDE EFFECTS:
------------
Logs to LOG_FILENAME resultq (or errorq) of the program and displays it if verbose mode


KNOWN BUGS:
----------
- Sometimes get_location returns '' as location, and hence the forecast displayed is for city_default
- TIDE_URL works only for some cities on the French West coast and returns no data if the city is not recognised (and sometimes the name should be CAPITALIZED) -- hence the option to force a city name with -tidename (list of cities here: http://www.horaire-maree.fr/)
- OPENWEATHER server works only for some cities and returns no data if the city is not recognised -- hence the option to force a city name with -weathername (list of cities is here: http://bulk.openweathermap.org/sample/city.list.json.gz)

"""


#-------------------------------------------------
#--- IMPORTS -------------------------------------
#-------------------------------------------------

from json import loads
from re import match
from time import strftime, sleep, timezone
from sys import exit, argv
import socket
from datetime import datetime
from calendar import Calendar
from requests import get
import urllib2 
from os import path, system
from configparser import ConfigParser

try:
	from psutil import cpu_percent
	has_psutil = True
except:
	has_psutil = False

import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

#-------------------------------------------------
#--- DEFINITIONS ---------------------------------
#-------------------------------------------------

PATH_PREFIX = path.dirname(path.abspath(__file__)) + '/'
LOG_FILENAME = PATH_PREFIX + "log_magicmirror.log"
CONFIG_FILENAME = PATH_PREFIX + 'config_magicmirror.conf'

NB_FORECAST = 6

MAX_ITER = 20  # Max nb of iteration of info fetching attempts
DELAY =  1200 # Delai between two retries in seconds

OPENWEATHER_FOR = "http://api.openweathermap.org/data/2.5/forecast?q=%s&units=metric&appid=%s"
OPENWEATHER_WEA = "http://api.openweathermap.org/data/2.5/weather?q=%s&units=metric&appid=%s"
TIDE_URL = "http://www.horaire-maree.fr/maree/%s/"
LOCATION_INFO = "http://ipinfo.io"
# ISS = "http://api.open-notify.org/iss-now.json"
CPU_TEMP_FILE = '/sys/class/thermal/thermal_zone0/temp'

HELP = "python mm_data.py [-h][-v][-city city[countrycode]][-tidename Name][-weathername Name]\n\
with:\n\
	-h: Display help info\n\
	-v: Verbose mode\n\
	-tide: Display tide info\
	-tidename: Name to be used when fetching tide info\n\
	-weathername: Name to be used when fetching weather info\n\
	-city city [countrycode]: Name (and countrycode) to be used for tide and weather, unless stated otherwise for weather or tide (defaut is city_default, country_default)"

WEATHER_CODE_MAPPING = {
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

WEATHER_CODE_MAPPING_FR = {
	"01d": "soleil",
	"01n": "nuit claire",
	"02d": "partiellement nuageux",
	"02n": "partiellement nuageux",
    "03d":	"nuages epars",
    "03n":	"nuages epars",
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

WEEKDAYS = {
	"1": "Mo",
	"2": "Tu",
	"3": "We",
	"4": "Th",
	"5": "Fr",
	"6": "Sa",
	"0": "Su"
}

WEEKDAYS_FR = {
	"1": "Lu",
	"2": "Ma",
	"3": "Me",
	"4": "Je",
	"5": "Ve",
	"6": "Sa",
	"0": "Di"
}

MONTHLIST_FR = [
	u"Janvier",
	u"Février",
	u"Mars",
	u"Avril",
	u"Mai",
	u"Juin",
	u"Juillet",
	u"Août",
	u"Septembre",
	u"Octobre",
	u"Novembre",
	u"Décembre"
]

WEEKDAYFULL_FR = [
	"Dimanche",
	"Lundi",
	"Mardi",
	"Mercredi",
	"Jeudi",
	"Vendredi",
	"Samedi"
]

verbose = True

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


#-------------------------------------------------
#--- FUNCTIONS -----------------------------------
#-------------------------------------------------


#-------------------------------------------------
#		Useful functions
#-------------------------------------------------


def tolog(txt, forceprint=False):
	"""
		Logs events and prints it if forceprint = True
	"""
	txt = remove_non_ascii(txt)
	if verbose or forceprint:
		print(txt)
	now = strftime('%Y/%m/%d %H:%M:%S')
	msg = "%s\t%s" % (now, txt)
	with open(LOG_FILENAME, 'a') as file:
		file.write(msg + "\n")
	return


def decode_arg(argv):
	"""
		Decoding of the shell arguments
	"""
	global verbose, tide_display

	tolog("Decoding arguments...")
	city = ''
	country = country_default
	tide_city = ''
	weather_city = ''

	n = 1
	length = len(argv)
	while n < length:
		arg = argv[n]
		if arg == '-v':  # Verbose
			verbose = True
			tolog("Verbose mode")
		if arg == '-tide':  # Display tide info
			tide_display = True
			tolog("Tide display mode")
		elif arg == '-h':  # Display help
			tolog("Help requested")
			print(HELP)
			exit(0)
		elif arg == '-tidename':	# Set tide name
			tide_display = True
			if n == length:
				tolog("...error: param -tidename should be followed by a name", True)
			elif argv[n+1][0] == '-':
				tolog("...error: param -tidename should be followed by a name", True)
			else:
				tide_city = argv[n+1]
				if city == '':
					city = tide_city
				n += 1
				tolog("Set name for tide as %s" % (tide_city))
		elif arg == '-weathername':  # Set weather name
			if n == length:
				tolog("...error: param -weathername should be followed by a name", True)
			elif argv[n+1][0] == '-':
				tolog("...error: param -weathername should be followed by a name", True)
			else:
				weather_city = argv[n+1]
				n += 1
				if city == '':
					city = weather_city
				tolog("Set name for weather as %s" % (weather_city))
		elif arg == '-city':  # Set city name
			if n == length:
				tolog("...error: param -city should be followed by a name", True)
			elif argv[n+1][0] == '-':
				tolog("...error: param -city should be followed by a name", True)
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
			tolog("Errorenous option: %s" % (arg), True)
		n += 1
	return city, country, tide_city, weather_city


def ms_kmh(speed):
	"""
	Converts m/s in km/h
	"""
	return float(speed) * 3.6


def deg_dir(deg):
	"""
	Converts direction in degree into cardinal points
	"""
	if deg < 22.5:
		dir = 'N'
	elif deg < 57.5:
		dir = 'NE'
	elif deg < 102.5:
		dir = 'E'
	elif deg < 147.5:
		dir = 'SE'
	elif deg < 192.5:
		dir = 'S'
	elif deg < 237.5:
		dir = 'SO'
	elif deg < 282.5:
		dir = 'O'
	elif deg < 327.5:
		dir = 'NO'
	else:
		dir = 'N'
	return dir


def extract_text(line, st1, st2, pos0):
	"""
	Extracts from line after position pos0 the text between st1 and st2 (included)
	"""
	pos1 = line.find(st1, pos0)
	if pos1 == -1:
		return '', -1
	pos2 = line.find(st2, pos1 + len(st1))
	if pos2 == -1:
		return '', -1
	text = line[pos1 + len(st1):pos2]
	return (text, pos2)


def remove_non_ascii(text):
	"""
		Returns text where non-ascii chars have been removed
	"""
	if type(text) is unicode:
		text = ''.join(i for i in text if ord(i) < 128)
	return text

#-------------------------
# 		Function to retrieve configuration
#-------------------------

def load_config():
	"""
	Loads the config file
	"""
	global city_default, country_default
	global client_id, client_secret
	global openweather_ID
	global tide_display

	tolog("Loading the configuration file...")
	try:
		config = ConfigParser()
		config.read(CONFIG_FILENAME)

		# LOCATION paramaters

		city_default = config.get('LOCATION', 'cityDefault')  
		country_default = config.get('LOCATION', 'countryDefault')  

		# GOOGLEID parameters

		client_id = config.get('GOOGLEID', 'clientID')	
		client_secret = config.get('GOOGLEID', 'clientSecret')	

		# OPENWEATHER parameters

		openweather_ID = config.get('OPENWEATHER', 'openWeatherID') 

		# FLAGS parameters

		tide_display = config.getboolean('FLAGS', 'tideDisplay')
		tolog("...loading of the config file ok")

	except Exception as e:
		tolog('...error reading config file %s, SORRY: %s' %
		      (CONFIG_FILENAME, e), True)
		exit()
	return


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
			tolog("...error fetching location info: status %s" % (result), True)
	except Exception as e:
		tolog("...error fetching location info: %s" % (e), True)

	return city, country


def retrieve_location():
	for i in range(MAX_ITER):
		city, country = get_location()
		if city != '':
			break
		sleep(DELAY)
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
		tolog("...error fetching weather info: %s" %(e), True)
		return {}


def get_weather(city, country, openweather_ID):
	"""
		Fetches current weather info and returns UTC and time of the weather, temperature, name and code of the weather condition
	"""

	weather_data = {}

	location_string = city + ',' + country

	tzone = -3600 + timezone
	tolog("Delta Timezone = %s" %(tzone))

 	#----- Extract current weather data

	tolog("Fetching current weather...")

	weather_current = fetch_weather(OPENWEATHER_WEA %(location_string, openweather_ID))
	if weather_current == {}:
		tolog("...error reading weather info: cannot read current weather", True)
	else:
		tolog("...current weather retrieved")
		try:
			temp_current = weather_current["main"]["temp"]
			tolog("...temperature %s" % (temp_current))
		except:
			temp_current = '?'
		try:
			press_current = weather_current["main"]["pressure"]
			tolog("...pression %s" % (press_current))
		except:
			press_current = '?'
		try:
			humi_current = weather_current["main"]["humidity"]
			tolog("...humidité %s" % (humi_current))
		except:
			humi_current = '?'
		try:
			wind_current = ms_kmh(weather_current["wind"]["speed"])
			tolog("...vent %s" % (wind_current))
		except:
			wind_current = '?'
		try:
			wind_dir = deg_dir(weather_current["wind"]["deg"])
			tolog("...direction %s" % (wind_dir))
		except:
			wind_dir = '?'
		try:
			sunrise = datetime.utcfromtimestamp(int(weather_current["sys"]["sunrise"])-tzone).strftime('%H:%M')
			sunset = datetime.utcfromtimestamp(int(weather_current["sys"]["sunset"])-tzone).strftime('%H:%M')
			tolog("...sunrise %s, sunset %s" % (sunrise, sunset))
		except:
			sunrise = '?'
			sunset = '?'
		try:
			utc = int(weather_current["dt"])
			time_current = datetime.utcfromtimestamp(utc-tzone).strftime('à %H:%M')
			tolog("...hour %s" % (time_current))

			code_current = remove_non_ascii(weather_current["weather"][0]["icon"])
			# code_current = "01d"
			if code_current in WEATHER_CODE_MAPPING:
				if country == 'Fr':
					weather_cur = WEATHER_CODE_MAPPING_FR[code_current]
				else:
					weather_cur = WEATHER_CODE_MAPPING[code_current]
			else:
				weather_cur = '?'
			tolog("...current weather is %s" % (weather_cur))
			tolog("...current code is %s" % (code_current))
			weather_data = {
				'utc': utc,
				'time': time_current,
				'temp': temp_current,
				'wind': wind_current,
				'wind_dir': wind_dir,
				'press': press_current,
				'humi': humi_current,
				'condition_code': code_current,
				'condition_name': weather_cur,
				'sunrise': sunrise,
				'sunset': sunset
			}

		except Exception as e:
			tolog("...error reading current weather: %s" % (e), True)

	return weather_data


def retrieve_weather(weather_city, country, openweather_ID):
	for i in range(MAX_ITER):
		weather_data = get_weather(weather_city, country, openweather_ID)
		if weather_data != {}:
			break
		sleep(DELAY)
	return weather_data


#-------------------------------------------------
#		Forecast functions
#-------------------------------------------------

def get_forecast(city, country, openweather_ID):
	"""
		Fetches forecast weather info for city, country, for the days following UTC
	"""
	forecast_data = {}
	location_string = city + ',' + country

	#----- Extract weather forecast data

	tolog("Attempting to fetch forecast")
	weather_forecast = fetch_weather(OPENWEATHER_FOR % (location_string, openweather_ID))

	if weather_forecast == {} : # or weather_current == {}:
		tolog("...error reading weather info: cannot read forecast weather", True)
		return {}

	try:
		forecast_list = weather_forecast["list"]
		day_num = -1
		wd = ''
		for i in range(len(forecast_list)):
			utc = int(forecast_list[i]["dt"])
			dt = datetime.utcfromtimestamp(utc)
			wd_new = dt.strftime('%w')
			hr = dt.strftime('%H')
			try:
				temp = forecast_list[i]["main"]["temp"]
			except:
				temp = '?'
			try:
				wind = ms_kmh(forecast_list[i]["wind"]["speed"])
			except:
				wind = '?'
			try:
				wind_dir = deg_dir(forecast_list[i]["wind"]["deg"])
			except:
				wind_dir = '?'
			try:
				code = remove_non_ascii(forecast_list[i]["weather"][0]["icon"])
				weather_name = WEATHER_CODE_MAPPING_FR[code]
			except:
				weather_name = '?'
			if wd != wd_new:
				wd = wd_new
				day_num += 1
				
				forecast_data[day_num] = {
					'weekday': wd,
					'nameday': WEEKDAYS_FR[wd],
					'hours': {},
					'temp_min' : temp,
                    'temp_max' : temp,
					'wind_max' : wind,
					'wind_max_dir': wind_dir
				}
			else:
				if temp != '?':
					if (forecast_data[day_num]['temp_max'] == '?') or (temp > forecast_data[day_num]['temp_max']):
						forecast_data[day_num]['temp_max'] = temp
					if (forecast_data[day_num]['temp_max'] == '?') or (temp < forecast_data[day_num]['temp_min']):
						forecast_data[day_num]['temp_min'] = temp
				if wind != '?':
					if (forecast_data[day_num]['wind_max'] == '?') or (wind > forecast_data[day_num]['wind_max']):
						forecast_data[day_num]['wind_max'] = wind
						forecast_data[day_num]['wind_max_dir'] = wind_dir

			forecast_data[day_num]['hours'][hr] = {
				'temp': temp,
				'wind': wind,
				'wind_dir': wind_dir,
				'condition_code': code,
				'condition_name': weather_name
			}

	except Exception as e:
		tolog("...error reading forecast weather: %s" % (e), True)
	return forecast_data


def retrieve_forecast(weather_city, country, openweather_ID):
	for i in range(MAX_ITER):
		forecast_data = get_forecast(weather_city, country, openweather_ID)
		if forecast_data != {}:
			break
		sleep(DELAY)
	return forecast_data


#-------------------------------------------------
#		Tide functions
#-------------------------------------------------

#---- Fetch tide info

def get_tide(city):

	tide_hours = []
	tide_coef = ''

	tolog("Fetching tide info...")
	try:
		req = urllib2.Request(TIDE_URL % (city))
		response_url = urllib2.urlopen(req)
	# except urllib2.URLError as e:
	# 	if hasattr(e, 'reason'):  # One reason (unsure what!)
	# 		error = e.reason
	# 	elif hasattr(e, 'code'):  # Another reason (unsure what!)
	# 		error = e.code
	except Exception as error:
		tolog("...error accessing tide server: %s" % (error), True)
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
	except Exception as e:
		tolog(e, True)
	return ([], '?')


def retrieve_tide(tide_city):
	for i in range(MAX_ITER):
		tide_hours, tide_coef = get_tide(tide_city)
		if tide_coef != '':
			break
		sleep(DELAY)
	return tide_hours, tide_coef


#-------------------------------------------------
#		ISS functions
#-------------------------------------------------

# TOLERANCE = 1
# # from geopy.geocoders import Nominatim


# def get_longlat(city, country):
# 	geolocator = Nominatim()
# 	home = geolocator.geocode(city + ", " + country)
# 	if home == {}:
# 		return 0, 0
# 	lat = float(home.latitude)
# 	long = float (home.longitude)
# 	return long, lat


# def test_iss(city, country):
# 	try:
# 		r = get(ISS)
# 		pos = r.json()['iss_position']
# 		lat_iss = float(pos['latitude'])
# 		long_iss = float(pos['longitude'])
# 		tolog("Long & Lat ISS = %s, %s" %(long_iss, lat_iss))
# 		long, lat = get_longlat(city, country)
# 		return (abs(lat_iss - lat) < TOLERANCE and abs(long_iss - long) < TOLERANCE)
# 	except Exception as e:
# 		tolog("Can't retrieve ISS info: %s" %(e))
# 		return False


#-------------------------------------------------
#		IP functions
#-------------------------------------------------

#---- Read CPU temerature & laod

def get_cpu_temp():
	if has_psutil:
		CPU_temp = CPU_TEMP_FILE

		with open(CPU_temp, "r") as temp_file:
			temp = float(temp_file.read())/1000
	else:
		temp = 0
	return temp


def get_cpu_percent():
	if has_psutil:
		pc = cpu_percent()
	else:
		pc = 0
	return pc


#---- Read local IP

def get_local_ip():
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.connect(("8.8.8.8", 80))
		ip_num = sock.getsockname()[0]
		sock.close()
		return ip_num
	except Exception as e:
		return "(unkown)"


#---- Read global IP

def get_public_ip():
	try:
		public_ip = urllib2.urlopen('http://ip.42.pl/raw').read()
		return public_ip
	except Exception as e:
		return "(unkown)"



#---- Retrieve IP information 

def retrieve_IP():

	for i in range(MAX_ITER):
		local_IP = get_local_ip()
		if local_IP != '':
			break
		sleep(DELAY)

	for i in range(MAX_ITER):
		public_IP = get_public_ip()
		if public_IP != '':
			break
		sleep(DELAY)

	cpu_temp = get_cpu_temp()
	cpu_load = get_cpu_percent()

	return local_IP, public_IP, cpu_temp, cpu_load


#-------------------------------------------------
#		Calendar functions
#-------------------------------------------------


def get_cal(country):
	n = datetime.now()
	cal = Calendar()
	month_cal = cal.monthdayscalendar(n.year, n.month)
	if country == 'Fr':
		day_list = WEEKDAYS_FR
	else:
		day_list = WEEKDAYS
	return month_cal, day_list


def get_date(country):
	if country == 'Fr':
		return WEEKDAYFULL_FR[int(strftime('%w'))]
	else:
		return strftime('%A')


def get_month(country):
	if country == 'Fr':
		return MONTHLIST_FR[int(strftime('%-m'))-1] + strftime(' %Y')
	return strftime('%B %Y')


def fetch_google_events():
	"""
	Fetches the start and name of the next events on the user's calendar.
	"""

	tolog("Fetching Google calendar...")
	try:
		creds = None
		# The file token.pickle stores the user's access and refresh tokens, and is
		# created automatically when the authorization flow completes for the first
		# time.
		if path.exists(PATH_PREFIX + 'token.pickle'):
			with open(PATH_PREFIX + 'token.pickle', 'rb') as token:
				creds = pickle.load(token)
		# If there are no (valid) credentials available, let the user log in.
		if not creds or not creds.valid:
			if creds and creds.expired and creds.refresh_token:
				creds.refresh(Request())
			else:
				flow = InstalledAppFlow.from_client_secrets_file(
					PATH_PREFIX + 'credentials.json', SCOPES)
				creds = flow.run_local_server(port=0)
			# Save the credentials for the next run
			with open(PATH_PREFIX + 'token.pickle', 'wb') as token:
				pickle.dump(creds, token)

		service = build('calendar', 'v3', credentials=creds)

		# Call the Calendar API
		now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
		events_result = service.events().list(calendarId='primary', timeMin=now,
										maxResults=10, singleEvents=True,
										orderBy='startTime').execute()
		events = events_result.get('items', [])

		event_list = []
		# if iss_inview:
		# 	event_name = {
		# 		'date': strftime('%Y-%m-%d'),
		# 		'time': strftime('Actuellement'),
		# 		'tz': '',
		# 		'start': '',
		# 		'summary': 'Station spaciale en vue'
		# 	}
		# 	event_list.append(event_name)

		for event in events:
			start = event['start'].get('dateTime', event['start'].get('date'))
			date_time = start.split('T')
			# date = date_time[0]
			wd = datetime.strptime(date_time[0], '%Y-%m-%d').strftime("%w")
			date_d = datetime.strptime(date_time[0], '%Y-%m-%d').strftime("%d")
			date = WEEKDAYS_FR[wd] + " " + date_d
			if len(date_time) > 1:
				time_tz = date_time[1]
				if len(time_tz) > 9:
					time = time_tz[0:8]
					tz = time_tz[9:]
				else:
					time = time_tz
					tz = ''
			else:
				time = ''
				tz = ''

			event_name = {
				'date': date,
				'time': time,
				'tz': tz,
				'start': start,
				'summary': event['summary']
			}
			event_list.append(event_name)
		return event_list

	except Exception as e:
		tolog("...error fetching calendar: %s" % (e), True)
		return []

#-------------------------------------------------
#		Main function for shell command
#-------------------------------------------------

if __name__ == "__main__":

	tolog("==== Fetching of weather and tide info")

	load_config()

	city, country, tide_city, weather_city = decode_arg(argv)

	if city == "":
		for i in range(MAX_ITER):
			city, country = get_location()
			if city != "":
				break
			sleep(DELAY)
	
	if city == "":
		tolog("Too many attemps to fetch location info, I settle for %s, %s" %(city_default, country_default))
		city = city_default
		country = country_default
	
	if tide_display:
		print("=== Tide and weather info for %s (%s) ===" %(city, country))
		
		if tide_city == '':
			tide_city = city
		
		tolog("Fetching tide info for %s" %(tide_city))
		for i in range(MAX_ITER):
			tide_hours, tide_coef = get_tide(tide_city)		
			if tide_coef != '':
				break
			sleep(DELAY)

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
	else:
		print("=== Weather & forecast info for %s (%s) ===" % (city, country))

	if weather_city == '':
		weather_city = city

	tolog("Fetching weather info for %s (%s)" % (weather_city, country))
	for i in range(MAX_ITER):
		weather_data = get_weather(weather_city, country, openweather_ID)
		if weather_data != {}:
			break
		sleep(DELAY)

	if weather_data == {}:
		tolog("Too many attemps to fetch weather info, I give up!")
	else:
		print("\nWeather info for %s (%s)" % (weather_city, country))
		print("Weather time: %s" % (weather_data['time']))
		print("Temperature: %s" % (weather_data['temp']))
		print("Weather condition: %s (code %s)" %(weather_data['condition_name'], weather_data['condition_code']))

		tolog("Fetching forecast info for %s (%s)" % (weather_city, country))
		for i in range(MAX_ITER):
			forecast_data = get_forecast(weather_city, country, openweather_ID)
			if forecast_data != {}:
				break
			sleep(DELAY)

		if forecast_data == {}:
			tolog("Too many attemps to fetch forecast info, I give up!")
		else:
			print("\nForecast info for %s (%s)" % (weather_city, country))
			for day in range(NB_FORECAST):
				daily_forecast = forecast_data[day]
				for utc_time in daily_forecast['hours']:
					print("For %s at %s: Weather is %s, temperature is %s" % (
						daily_forecast['nameday'],
						utc_time,
						daily_forecast['hours'][utc_time]['condition_name'],
						daily_forecast['hours'][utc_time]['temp'])
					)

	event_list = fetch_google_events()
	i = 1
	for event in event_list:
		print("Event #%s: Date = %s, Start = %s, Summary = %s" %
		      (i, event['date'], event['start'], event['summary']))
		i += 1

#-------------------------------------------------
#----- END OF THE PROGRAMME ----------------------
#-------------------------------------------------
