#!/usr/bin/env python
# -*- coding: utf-8 -*-

#---------------------------------------------------#
#													#
#				magicmirror.py						#
#				by N.Mercouroff						#
#													#
#---------------------------------------------------#

version_prog = "200720"
name_prog = "magicmirror.py"


"""
Version: 20/7/19

Python program for displaying information on a "magic mirror", ie, an e-ink screen, connected to a Raspberry Pi Zero

Information displayed includes:
- local and global IP address and CPU info
- local weather, ephemeris, and forecast for 7 days (from openweather  server)
- local tide hours (if relevant, grabbed from horaire-maree web server)
- current calendar

HISTORY:
--------
20/7/20:
- Added config file
- Cleanup of the code

15/9/19:
- Adaptation à l'écran inkyWHAT de Pimoroni

3/8/19:
- First development, derivated from inky_weather_tide.py project


USAGE:
-----
From the shell: 
python magicmirror.py [-city city [countrycode]] [-h] [-v] [-tidename Name] [-weathername Name] [-tide] [-p] with:
	-h: Display help info
	-v: Verbose mode
	-p: Print only mode (no display on Inky)
	-info: Display screen with IP info before weather
	-tide: Display daily tide info in place of current weather
	-tidename: Name to be used when fetching tide info (if different from city)
	-weathername: Name to be used when fetching weather info (if different from city)
	-city city [countrycode]: Name (and countrycode) to be used for title, tide and weather, unless stated otherwise for weather or tide (defaut is city_default, country_default)


From another python program: 
inky_weather_tide(city, country, info_display=False, tide_display=False, rotate=True, tidename='', weathername='')
Where:
	- city : name of the city where forcast shall be displayed (default is either local weather, as determined by IP, or city_default)
	- country : code of the country (default is country_default)
	- info_display : display IP info before the weather info
	- tide_display : display tide and forecast info instead of current weather and forecat info
	- rotate : rotate 180° the display
	- tidename: Name to be used when fetching tide info (if different from city)
	- weathername: Name to be used when fetching weather info (if different from city)


EXAMPLE:
-------
In the crontab:

@reboot sudo python /home/pi/Magic/magicmirror.py -city Paris -info
0 7 * * * sudo python /home/pi/Magic/magicmirror.py -city Paris 

python magicmirror.py -city Ouessant -weathername Brest -tidename OUESSANT -wind


PREREQUISITS:
------------
Requires in current directory a subdirectory /resources with icon PNG files:
- icon-cloud.png: cloudy
- icon-part_cloud.png: partly cloudy
- icon-rain.png: raining
- icon-snow.png: snowing
- icon-storm.png: thunderstorm
- icon-sun.png: sunny
- icon-clear_nite.png: clear night
- icon-wind.png: windy
- icon-myst.png: Fog

Requires the following standard modules:
- time, sys, datetime, os, configparser

Requires the following sub-programs and files:
- panic.py : to prevent re-entering of the code
- mm_data : to fetch weather, tide and calendar information 
- mm_display : to display information on the inky HAT / wHAT
- config_magicmirror.conf : configuration data

Installation of the lib:
	pip install ConfigParser


SIDE EFFECTS:
------------
Logs to LOG_FILENAME results (or errors) of the program and displays it if verbose mode


KNOWN BUGS:
----------
- Sometimes get_location returns '' as location, and hence the forecast displayed is for city_default
- TIDE_URL works only for some cities on the French West coast and returns no data if the city is not recognised (and sometimes the name should be CAPITALIZED) -- hence the option to force a city name with -tidename (list of cities here: http://www.horaire-maree.fr/)
- OPENWEATHER server works only for some cities and returns no data if the city is not recognised -- hence the option to force a city name with -weathername (list of cities is here: http://bulk.openweathermap.org/sample/city.list.json.gz)

"""


#-------------------------------------------------
#--- IMPORTS -------------------------------------
#-------------------------------------------------


from time import strftime, sleep
import sys
from datetime import datetime
import mm_data
import mm_display
from os import path
import panic
from configparser import ConfigParser


#-------------------------------------------------
#--- DEFINITIONS ---------------------------------
#-------------------------------------------------

PATH_PREFIX = path.dirname(path.abspath(__file__)) + '/'
LOG_FILENAME = PATH_PREFIX + "log_magicmirror.log"
CONFIG_FILENAME = PATH_PREFIX + 'config_magicmirror.conf'

HELP = """
python %s [-h][-city city[countrycode]][-v][-tidename Name][-weathername Name][-tide][-p] with:
	-h: Display help info
	-v: Verbose mode
	-p: Print only mode(no display on Inky)
	-info: Display screen with IP info before weather
	-tide: Display daily tide info in place of current weather
	-tidename: Name to be used when fetching tide info
	-weathername: Name to be used when fetching weather info
	-wind: Show wind info
	-city city [countrycode]: Name (and countrycode) to be used for title, tide and weather, unless stated otherwise for weather or tide (defaut is city_default, country_default)" % (name_prog)
"""

verbose = False

NB_FORECAST = 5  # Nb of days of forecast
DELAY_INFO = 5  # Delay for displaying info in seconds


#-------------------------------------------------
#--- FUNCTIONS -----------------------------------
#-------------------------------------------------

#-------------------------------------------------
#		Useful functions
#-------------------------------------------------

def remove_non_ascii(text):
	"""
		Returns text where non-ascii chars have been removed
	"""
	if type(text) is unicode:
		text = ''.join(i for i in text if ord(i) < 128)
	return text


def tolog(txt, forceprint = False):
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
	global verbose

	tolog("Decoding arguments...")
	city = ''
	country = country_default
	tidename = ''
	weathername = ''
	tide_display = False
	info_display = False
	weather_display = True
	wind_display = False
	no_display = False
	iss = False
	today = ''

	n = 1
	length = len(argv)
	while n < length:
		arg = argv[n]
		if arg == '-v':  # Verbose
			verbose = True
			tolog("Verbose mode", True)
		elif arg == '-h':  # Display help
			tolog("Help requested", True)
			print(HELP)
			sys.exit(0)
		elif arg == '-p':  # Print only
			no_display = False
			tolog("No display_mm mode", True)
		elif arg == '-tide':    # Tide mode
			tide_display = True
			tolog("Tide display mode", True)
		elif arg == '-wind':    # Tide mode
			wind_display = True
			tolog("Wind display mode", True)
		elif arg == '-info':    # Display info at boot
			info_display = True
			tolog("Info display mode", True)
		elif arg == '-iss':    # Display iss
			iss = True
			tolog("ISS display mode", True)
		elif arg == '-tidename':  # Set tide name
			tide_display = True
			if n == length:
				tolog("Error: param -tidename should be followed by a name", True)
			elif argv[n+1][0] == '-':
				tolog("Error: param -tidename should be followed by a name", True)
			else:
				tidename = argv[n+1]
				if city == '':
					city = tidename
				n += 1
				tolog("Set name for tide as %s" % (tidename), True)
		elif arg == '-day':  # Set day
			if n == length:
				tolog("Error: param -day should be followed by a date", True)
			elif argv[n+1][0] == '-':
				tolog("Error: param -day should be followed by a date", True)
			else:
				today = argv[n+1]
				n += 1
				tolog("Set day as %s" % (today), True)
		elif arg == '-weathername':  # Set weather name
			if n == length:
				tolog("Error: param -weathername should be followed by a name", True)
			elif argv[n+1][0] == '-':
				tolog("Error: param -weathername should be followed by a name", True)
			else:
				weathername = argv[n+1]
				n += 1
				if city == '':
					city = weathername
				tolog("Set name for weather as %s" % (weathername))
		elif arg == '-city':  # Set city name
			if n == length:
				tolog("Error: param -city should be followed by a name", True)
			elif argv[n+1][0] == '-':
				tolog("Error: param -city should be followed by a name", True)
			else:
				n += 1
				city = argv[n]
				tolog("Set city name as %s" % (city), True)
				if n+1 < length:
					if not argv[n+1][0] == '-':
						n += 1
						country = argv[n]
						tolog("Set country name as %s" % (country), True)
		elif arg == '-noweather':
			weather_display = False
			tolog("No weather displayed", True)
		elif arg[0] == '-':
			tolog("Errorenous option: %s" % (arg), True)
		n += 1
	return city, country, info_display, tide_display, weather_display, wind_display, no_display, iss, tidename, weathername, today


#-------------------------
# 		Function to retrieve configuration
#-------------------------

def load_config():
	"""
	Loads the config file
	"""
	global city_default, country_default, rotate, openweather_ID

	tolog("Loading the configuration file...")
	try:
		config = ConfigParser()
		config.read(CONFIG_FILENAME)

		# LOCATION paramaters

		city_default = config.get('LOCATION', 'cityDefault')  
		country_default = config.get('LOCATION', 'countryDefault')  

		# FLAGS parameters

		rotate = config.getboolean('FLAGS', 'rotate')
		tolog("...loading of the config file ok")

		# OPENWEATHER parameters

		openweather_ID = config.get('OPENWEATHER', 'openWeatherID')

	except Exception as e:
		tolog('...error reading config file %s, SORRY: %s' % (CONFIG_FILENAME, e), True)
		exit()
	return


#-------------------------------------------------
#		Functions to retrieve information
#-------------------------------------------------

def fetch_location():

	tolog("Fetching location info...")
	city, country = mm_data.retrieve_location()

	if city == "":
		tolog("...cannot retrieve location info, I settle for %s, %s" %(city_default, country_default))
		city = city_default
		country = country_default
	else:
		tolog("...CITY = %s, COUNTRY = %s" %(city, country))
	return city, country
	

def fetch_IP():

	tolog("Fetching IP & info...")
	local_IP, public_IP, cpu_temp, cpu_load = mm_data.retrieve_IP()

	local_IP = "IP loc.: %s" % (local_IP)
	tolog("...local IP : " + local_IP)

	public_IP = "IP pub.: %s" % (public_IP)
	tolog("...public IP : " + public_IP)

	info_CPU = "CPU: T. {:2.0f} C, load {:2.0f} %".format(cpu_temp, cpu_load)
	tolog("...CPU info : " + info_CPU)

	return local_IP, public_IP, info_CPU


def fetch_calendar(city, country, today):
	tolog("Fetching calendar info for %s..." % (city))
	month_cal, day_list = mm_data.get_cal(country)
	monthname = mm_data.get_month(country)
	if today == '':
		today = strftime("%-d")
	event_list = mm_data.fetch_google_events()

	i = 1
	for event in event_list:
		tolog("Event #%s: Date = %s, Start = %s, Summary = %s" % (i, event['date'], event['start'], event['summary']))
		i+= 1

	return month_cal, day_list, monthname, today, event_list


def fetch_tide(tide_city):

	tolog("Fetching tide info for %s..." % (tide_city))
	tide_hours, tide_coef = mm_data.retrieve_tide(tide_city)

	if tide_coef == '' or tide_coef == '?':
		tolog("...cannot retrieve tide info")
	else:
		tolog("...tide info for %s:" % (tide_city))
		tolog("Tide coefficient: %s" % (tide_coef))
		if len(tide_hours) == 1:
			tolog("Hightide time: %s" % (tide_hours[0]))
		elif len(tide_hours) == 2:
			tolog("First hightide time: %s" % (tide_hours[0]))
			tolog("Second hightide time: %s" % (tide_hours[1]))
	return tide_hours, tide_coef


def fetch_weather(weather_city, country):

	tolog("Fetching weather info for %s (%s)..." % (weather_city, country))
	weather_data = mm_data.retrieve_weather(weather_city, country, openweather_ID)

	if weather_data == {}:
		tolog("...cannot retrieve weather info")
	else:
		tolog("...weather info:")
		tolog("Weather time: %s" % (weather_data['time']))
		tolog("Temperature: %s" % (weather_data['temp']))
		tolog("Weather condition: %s (%s)" %(weather_data['condition_name'], weather_data['condition_code']))
	return weather_data


def fetch_forecast(weather_city, country):

	tolog("Fetching forecast info for %s (%s)..." % (weather_city, country))
	forecast_data = mm_data.retrieve_forecast(weather_city, country, openweather_ID)

	if forecast_data == {}:
		tolog("...cannot retrieve forecast info")
	else:
		tolog("...forecast info:")
		for day in range(NB_FORECAST):
			daily_forecast = forecast_data[day]
			for utc_time in daily_forecast['hours']:
				tolog("For %s at %s: Weather is %s, temperature is %s" % (
					daily_forecast['nameday'],
					utc_time,
					daily_forecast['hours'][utc_time]['condition_name'],
					daily_forecast['hours'][utc_time]['temp'])
				)

	return forecast_data


def fetch_title(city, country):
	week_day = mm_data.get_date(country)
	title = city + ', ' + week_day + strftime(' %-d/%-m a %H:%M')
	return title


#-------------------------------------------------
#		Main function for shell command
#-------------------------------------------------

def magicmirror_main(city, country, info_display=False, tide_display=False, weather_display=True, wind_display=False, no_display=False, iss=False, rotate=True, tide_city='', weather_city='', today=''):

	if not no_display:
		ok = mm_display.draw_init(rotate)

	if info_display:
		local_IP, public_IP, info_CPU = fetch_IP()
		mm_display.display_IP(city, local_IP, public_IP, info_CPU)	
		ok = mm_display.display_show()
		sleep(DELAY_INFO)

	if weather_city == '':
		weather_city = city

	if tide_display:
		if tide_city == '':
			tide_city = city
		tide_hours, tide_coef = fetch_tide(tide_city)
		if tide_coef == '' or tide_coef == '?':
			tide_display = False

	weather_data = fetch_weather(weather_city, country)
	forecast_data = fetch_forecast(weather_city, country)
	month_cal, day_list, monthname, today, event_list = fetch_calendar(city, country, today)
	title = fetch_title(city, country)

	if no_display:
		return True

	ok = mm_display.init_display(wind_display)
	if tide_display:
		ok = mm_display.display_tide(tide_hours, tide_coef, country)
	else:
		ok = mm_display.display_ephem(weather_data, country)
	ok = mm_display.display_weather(weather_data, wind_display)
	ok = mm_display.display_forecast(forecast_data, wind_display)

	# if not iss:
	# 	iss = mm_data.test_iss(city, country)

	ok = mm_display.display_calendar(month_cal, day_list, monthname, today, event_list, wind_display)
	ok = mm_display.display_title(title)
	ok = mm_display.display_show()

	return ok


if __name__ == "__main__":

	tolog("*** Info display start ***", True)

	ok, err = panic.test_panic(False)
	if not ok:
		tolog(err, True)
		sys.exit()

	load_config()

	city, country, info_display, tide_display, weather_display, wind_display, no_display, iss, tidename, weathername, today = decode_arg(sys.argv)

	if city == "":
		city, country = fetch_location()

	ok = magicmirror_main(city, country, info_display, tide_display, weather_display,
	                      wind_display, no_display, iss, rotate, tidename, weathername, today)

	if ok:
		tolog("Weather info for %s in %s displayed ; enjoy !" % (city, country), True)
	else:
		tolog("Coulnd't display weather info for %s in %s ; sorry !" % (city, country), True)

	ok, err = panic.delete_panic()
	if not ok:
		tolog(err, True)


#-------------------------------------------------
#----- END OF THE PROGRAMME ----------------------
#-------------------------------------------------
