#!/usr/bin/env python
# -*- coding: utf-8 -*-

#---------------------------------------------------#
#													#
#				inky_weather_tide.py				#
#													#
#---------------------------------------------------#

"""
Version: 17/2/19

Python program for fetching weather info on openweather web server and tide info on horaire-maree web server and displaying them on an Inky screen connected to a Raspberry Pi Zero

HISTORY:
--------
17/2/19:
- Split fetching weather, forecast and tide info from the main program to display the info

13/2/19:
- Added option to display of tide instead of current wethear
- Added otpion to display IP info before weather info

10/2/19:
- Rewriting of the program for fetching data on OpenWeather site

4/9/18:
- Change title format to display date as well as hour of forecast

29/8/18:
- Corrected icon directory name into absolute path 

25/6/18:
- Added a new icon to illustrate weather forecast of type "fair night"

9/6/18:
- Corrected a bug with PM/AM for Noon and Midnight

3/6/18:
- Added "rotate" value to force screen rotation
- Added test for countrycode to display names in French if country is France

2/6/18:
- Initial program, derivated from a previous work, and a weather.py program distributed along with Inky screen as an example (source: https://github.com/pimoroni/inky-phat/blob/master/examples/weather.py)


USAGE:
-----
From the shell: 
python inky_weather.py [-city city [countrycode]] [-h] [-v] [-tidename Name] [-weathername Name] [-tide] [-p] with:
	-h: Display help info
	-v: Verbose mode
	-p: Print only mode (no display on Inky)
	-info: Display screen with IP info before weather
	-tide: Display daily tide info in place of current weather
	-tidename: Name to be used when fetching tide info
	-weathername: Name to be used when fetching weather info
	-city city [countrycode]: Name (and countrycode) to be used for title, tide and weather, unless stated otherwise for weather or tide (defaut is CITY_DEFAULT, COUNTRY_DEFAULT)

From another python program: 
inky_weather.inky_weather(city, country, info_display=False, tide_display=False, rotate=True, tidename='', weathername='')

Where:
- city : name of the city where forcast shall be displayed (default is either local weather, as determined by IP, or CITY_DEFAULT)
- country : code of the country (default is 'FR' for France)
- info_display : 


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


from glob import glob
from json import loads
from re import match
from time import strftime, sleep
import sys
from datetime import datetime
from PIL import Image, ImageFont
from requests import get
from urllib2 import Request, urlopen, URLError

has_inky = True
try:
	import inkyphat
except:
	has_inky = False
	print("No inky")

import inky_IP, weather_tide

#-------------------------------------------------
#--- DEFINITIONS ---------------------------------
#-------------------------------------------------

nb_forecast = 4
nb_iter = 3  # Nb d'itérations max pour essayer d'afficher les info
delay = 30  # Delai entre deux itérations

PATH_FILENAME = "/home/pi/InkyWeather/"
LOG_FILENAME = "log_weather.log"
ICON_SOURCE = "resources/icon-*.png"

HELP = "python inky_weather.py [-h][-city city[countrycode]][-v][-tidename Name][-weathername Name][-tide][-p] with:\n\
	-h: Display help info\n\
	-v: Verbose mode\n\
	-p: Print only mode(no display on Inky)\n\
	-info: Display screen with IP info before weather\n\
	-tide: Display daily tide info in place of current weather\n\
	-tidename: Name to be used when fetching tide info\n\
	-weathername: Name to be used when fetching weather info\n\
	-city city [countrycode]: Name (and countrycode) to be used for title, tide and weather, unless stated otherwise for weather or tide (defaut is CITY_DEFAULT, COUNTRY_DEFAULT)"

icon_mapping = {
	"01d": "sun",
	"01n": "clear_nite",
	"02d": "part_cloud",
	"02n": "part_cloud",
	"03d": "cloud",
	"03n": "cloud",
	"04d": "cloud",
	"04n": "cloud",
	"09d": "rain",
	"09n": "rain",
	"10d": "rain",
	"10n": "rain",
	"11d": "storm",
	"11n": "storm",
	"13d": "snow",
	"13n": "snow",
	"50d": "myst",
	"50n": "myst"  
}

if has_inky:
	font18 = inkyphat.ImageFont.truetype(inkyphat.fonts.FredokaOne, 18)
	font20 = inkyphat.ImageFont.truetype(inkyphat.fonts.FredokaOne, 20)
	font24 = inkyphat.ImageFont.truetype(inkyphat.fonts.FredokaOne, 24)

rotate = True

icons = {}
masks = {}

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
	with open(PATH_FILENAME + LOG_FILENAME, 'a') as file:
		file.write(msg + "\n")
	return


def decode_arg(argv):
	global verbose, has_inky

	tolog("Decoding arguments...")
	city = ''
	country = COUNTRY_DEFAULT
	tidename = ''
	weathername = ''
	tide_display = False
	info_display = False

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
		elif arg == '-p':  # Print only
			has_inky = False
			tolog("No inky mode")
		elif arg == '-tide':    # Tide mode
			tide_display = True
			tolog("Tide display mode")
		elif arg == '-info':    # Display info at boot
			info_display = True
			tolog("Info display mode")
		elif arg == '-tidename':	# Set tide name
			tide_display = True
			if n == length:
				tolog("Error: param -tidename should be followed by a name")
			elif argv[n+1][0] == '-':
				tolog("Error: param -tidename should be followed by a name")
			else:
				tidename = argv[n+1]
				if city == '':
					city = tidename
				n += 1
				tolog("Set name for tide as %s" % (tidename))
		elif arg == '-weathername':  # Set weather name
			if n == length:
				tolog("Error: param -weathername should be followed by a name")
			elif argv[n+1][0] == '-':
				tolog("Error: param -weathername should be followed by a name")
			else:
				weathername = argv[n+1]
				n += 1
				if city == '':
					city = weathername
				tolog("Set name for weather as %s" % (weathername))
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
	return city, country, info_display, tide_display, tidename, weathername


#-------------------------------------------------
#		Main function to display forecast
#-------------------------------------------------

def init_display(rotate):
	global icons, masks

	if not has_inky:
		print("Information for %s:" % (city))
		return

	if rotate:
		inkyphat.set_rotation(180)

	#----- Loads icon files and generates masks
	for icon in glob(PATH_FILENAME + ICON_SOURCE):
		icon_name = icon.split("icon-")[1].replace(".png", "")
		icon_image = Image.open(icon)
		icons[icon_name] = icon_image
		masks[icon_name] = inkyphat.create_mask(icon_image)

	return 


def clear_display():
	if not has_inky:
		return

	inkyphat.clear()
	# inkyphat.rectangle((0, 31, 212, 104), inkyphat.WHITE, inkyphat.WHITE)
	return


def finish_display():

	if not has_inky:
		return

	inkyphat.line((52, 30, 52, 104), inkyphat.BLACK)
	inkyphat.show()

	return True


def display_title(text):

	now_time = strftime('%d/%m %H:%M')

	title_string = text + " " + now_time

	if not has_inky:
		print(title_string)
		return

	clear_display()
	inkyphat.rectangle((0, 0, 212, 30), inkyphat.RED, inkyphat.RED)
	width, height = font20.getsize(title_string)
	d, r = divmod(width, 2)
	inkyphat.text((106-d, 3), title_string, inkyphat.WHITE, font=font20)
	return


def display_weather(weather_data):
	"""
		Displays the weather data on inky display
	"""
	global icons, masks
	global inkyphat

	if weather_data['condition_code'] in icon_mapping:
		icon_current = icon_mapping[weather_data['condition_code']]
		tolog("...icon %s" % (icon_current))
	else:
		icon_current = None
		tolog("...no icon found")

	if not has_inky:
		print("Current weather:")
		print("Temperature = %s" % (weather_data['temp']))
		print("Time weather = %s" % (weather_data['time']))
		print("Condition = %s" % (weather_data['condition_name']))
		return True

	if icon_current is not None:
		inkyphat.paste(icons[icon_current], (8, 44), masks[icon_current])
	else:
		inkyphat.text((16, 54), "?", inkyphat.RED, font=font20)

	inkyphat.text((14, 84), u"{:.0f}°".format(weather_data['temp']), inkyphat.RED, font=font18)
	inkyphat.text((3, 32), weather_data['time'], inkyphat.BLACK, font=font18)

	return True


def display_forecast(forecast_data):
	"""
		Displays the forecast data on inky display
	"""
	global icons, masks
	global inkyphat

	if not has_inky:
		print("Forecast weather:")
		for day in range(nb_forecast):
			daily_forecast = forecast_data[day]
			print("For %s at Noon: Weather is %s, temperature is %s" % (
				daily_forecast['nameday'],
				daily_forecast['condition_name'],
				daily_forecast['temp']))
		return True

	for day in range(nb_forecast):
		daily_forecast = forecast_data[day]

		if daily_forecast['condition_code'] in icon_mapping:
			icon_current=icon_mapping[daily_forecast['condition_code']]
			tolog("...icon %s" % (icon_current))
		else:
			icon_current = None
			tolog("...no icon found")

		# Draw the current weather icon over the backdrop
		if icon_current is not None:
			inkyphat.paste(icons[icon_current], (52 + i*38, 44), masks[icon_current])
		else:
			inkyphat.text((56 + i*38, 54), "?", inkyphat.RED, font=font20)

		inkyphat.text((64 + i*38, 84),
		              u"{:.0f}°".format(daily_forecast['temp']), inkyphat.RED, font=font18)
		inkyphat.text((64 + i*38, 32),
		              daily_forecast['nameday'], inkyphat.BLACK, font=font18)

	return True


def display_tide(tide_hours, tide_coef, country):
	"""
		Displays the tide info on inky display
	"""
	if not has_inky:
		print("Current tide:")
		print("Tide hours: %s, %s" % (tide_hours[0], tide_hours[1]))
		print("Coefficient: %s" % (tide_coef))

		return True

	#----- Display tide info

	if country == 'Fr':
		high_tide = "PM:"
	else:
		high_tide = "Hi:"
	inkyphat.text((12, 31), high_tide, inkyphat.BLACK, font=font18)
	if len(tide_hours) > 0:
		inkyphat.text((2, 50), tide_hours[0], inkyphat.RED, font=font18)
	if len(tide_hours) > 1:
		inkyphat.text((2, 68), tide_hours[1], inkyphat.RED, font=font18)
	inkyphat.text((8, 84), '(' + tide_coef + ')', inkyphat.BLACK, font=font18)

	return(True)


#-------------------------------------------------
#		Main function for shell command
#-------------------------------------------------

def inky_weather(city, country, info_display=False, tide_display=False, rotate=True, tide_city='', weather_city=''):

	init_display(rotate)

	if info_display:
		inky_IP.display_info(city, False)	# No need for force rotation, already done in init
		sleep(delay)

	display_title(city)

	if tide_display:
		if tide_city == '':
			tide_city = city

		tolog("Fetching tide info for %s" % (tide_city))
		for i in range(nb_iter):
			tide_hours, tide_coef = weather_tide.get_tide(tide_city)
			if tide_coef != '':
				break
			sleep(delay)

		if tide_coef == '':
			tolog("Too many attemps to fetch tide info, I give up!")
		elif tide_coef == '?':
			tolog("Cannot fetch tide info for %s" % (tide_city))
		else:
			tolog("\nTide info for %s" % (tide_city))
			tolog("Tide coefficient: %s" % (tide_coef))
			if len(tide_hours) == 1:
				tolog("Hightide time: %s" % (tide_hours[0]))
			elif len(tide_hours) == 2:
				tolog("First hightide time: %s" % (tide_hours[0]))
				tolog("Second hightide time: %s" % (tide_hours[1]))
			tide_display = display_tide(tide_hours, tide_coef, country)

	if weather_city == '':
		weather_city = city

	tolog("Fetching weather info for %s (%s)" % (weather_city, country))
	for i in range(nb_iter):
		weather_data=weather_tide.get_weather(weather_city, country)
		if weather_data != {}:
			break
		sleep(delay)

	if weather_data == {}:
		tolog("Too many attemps to fetch weather info, I give up!")
		return False

	tolog("\nWeather info for %s (%s)" % (weather_city, country))
	tolog("Weather time: %s" % (weather_data['time']))
	tolog("Temperature: %s" % (weather_data['temp']))
	tolog("Weather condition: %s (code %s)" %(weather_data['condition_name'], weather_data['condition_code']))

	tolog("Fetching forecast info for %s (%s)" % (weather_city, country))
	for i in range(nb_iter):
		forecast_data = weather_tide.get_forecast(
		    weather_city, country, weather_data['utc'])
		if forecast_data != {}:
			break
		sleep(delay)

	if forecast_data == {}:
		tolog("Too many attemps to fetch forecast info, I give up!")
		return False

	tolog("Forecast info for %s (%s)" % (weather_city, country))
	for day in range(nb_forecast):
		daily_forecast = forecast_data[day]
		tolog("For %s at Noon: Weather is %s, temperature is %s" % (
			daily_forecast['nameday'],
			daily_forecast['condition_name'],
			daily_forecast['temp'])
		)

	if not tide_display:
		tolog("Displaying weather info...")
		display_weather(weather_data)

	tolog("Displaying forecast...")
	display_forecast(forecast_data)

	finish_display()

	return True


if __name__ == "__main__":

	tolog("Weather display started")

	city, country, info_display, tide_display, tidename, weathername = decode_arg(sys.argv)

	if city == "":
		for i in range(nb_iter):
			city, country = weather_tide.get_location()
			if city != "":
				break
			sleep(delay)

	if city == "":
		tolog("Too many attemps to fetch location info, I settle for %s, %s" %
                    (CITY_DEFAULT, COUNTRY_DEFAULT))
		city = CITY_DEFAULT
		country = COUNTRY_DEFAULT

	ok = inky_weather(city, country, info_display, tide_display, rotate, tidename, weathername)

	if ok:
		tolog("Weather info for %s in %s displayed ; enjoy !" % (city, country))
	else:
		tolog("Coulnd't display weather info for %s in %s ; sorry !" % (city, country))

#-------------------------------------------------
#----- END OF THE PROGRAMME ----------------------
#-------------------------------------------------
