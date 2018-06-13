#!/usr/bin/env python
# -*- coding: utf-8 -*-

#---------------------------------------------------#
#													#
#				inky_forecast.py					#
#													#
#---------------------------------------------------#

"""
Version: 9/6/18

Python program for fetching on Yahoo server and displaying weather forecast on an Inky screen connected to a Raspberry Pi Zero

HISTORY:
--------

9/6/18:
- Corrected a bug with PM/AM for Noon and Midnight

3/6/18:
- Added "rotate" value to force screen rotation
- Added test for countrycode to display names in French if country is France

2/6/18:
- Initial program, derivated from a previous work, and an weather.py program distributed along with Inky screen as an example (source: https://github.com/pimoroni/inky-phat/blob/master/examples/weather.py)


USAGE:
-----

From the shell: python inky_forecast.py [city [countrycode]]
From another python program: inky_forecast.display_forecast(city, countrycode)

Where:
- city is name of the city where forcast shall be displayed (default is local weather, as determined by IP)
- countrycode is code of the country (default is 'FR' for France)


PREREQUISITS:
------------

Requires in current directory a subdirectory /resources with icon PNG files:
- icon-cloud.png: cloudy
- icon-part_cloud.png: partly cloudy
- icon-rain.png: raining
- icon-snow.png: snowing
- icon-storm.png: thunderstorm
- icon-sun.png: sunny
- icon-wind.png: windy


SIDE EFFECTS:
------------

Prints on the terminal result (or error) of the program if in shell mode


KNOWN BUGS:
----------

- Sometimes get_location returns '' as location, and hence the forecast cannot be displayed

"""


#-------------------------------------------------
#--- IMPORTS -------------------------------------
#-------------------------------------------------


import glob
import json
import time, sys
import urllib
from PIL import Image, ImageFont
import email.utils
import requests
import inkyphat


#-------------------------------------------------
#--- DEFINITIONS ---------------------------------
#-------------------------------------------------

white = 0
black = 1
red = 2

nb_forecast = 4

icon_map = {
	"snow": [5, 6, 7, 8, 10, 13, 14, 15, 16, 17, 18, 41, 42, 43, 46],
	"rain": [9, 11, 12],
	"cloud": [19, 20, 21, 22, 25, 26, 27, 28],
	"part_cloud": [29, 30, 44],
	"sun": [32, 33, 34, 36],
	"storm": [0, 1, 2, 3, 4, 37, 38, 39, 45, 47],
	"wind": [23, 24]
}

weekdays = {
	"Mon": "Mo",
	"Tue": "Tu",
	"Wed": "We",
	"Thu": "Th",
	"Fri": "Fr",
	"Sat": "Sa",
	"Sun": "Su"
}

weekdays_FR = {
	"Mon": "Lu",
	"Tue": "Ma",
	"Wed": "Me",
	"Thu": "Je",
	"Fri": "Ve",
	"Sat": "Sa",
	"Sun": "Di"
}

font18 = inkyphat.ImageFont.truetype(inkyphat.fonts.FredokaOne, 18)
font20 = inkyphat.ImageFont.truetype(inkyphat.fonts.FredokaOne, 20)
font24 = inkyphat.ImageFont.truetype(inkyphat.fonts.FredokaOne, 24)

rotate = True

#-------------------------------------------------
#--- FUNCTIONS -----------------------------------
#-------------------------------------------------


#-------------------------------------------------
#		Useful functions
#-------------------------------------------------

#---- Fetch location

def get_location():
	res = requests.get('http://ipinfo.io')
	if (res.status_code == 200):
		json_data = json.loads(res.text)
		return json_data
	return {}



#---- Encode '+' in URL 

def url_encode(qs):
	val = ""
	try:	# Python 2
		val = urllib.urlencode(qs).replace("+","%20")
	except: # Python 3
		val = urllib.parse.urlencode(qs).replace("+", "%20")
	return val


def get_weather(address):
	base = "https://query.yahooapis.com/v1/public/yql?"
	query = "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text=\""+address+"\")"
	qs={"q": query, "format": "json", "env": "store://datatables.org/alltableswithkeys"}

	uri = base + url_encode(qs)

	try:
		res = requests.get(uri)
		if (res.status_code==200):
			json_data = json.loads(res.text)
			return json_data
		else:
			return {}
	except:
		return {}


#-------------------------------------------------
#		Main function to display forecast
#-------------------------------------------------

def display_forecast(CITY, COUNTRYCODE):

 #----- Fetch forecast data

	location_string = "{city}, {countrycode}".format(city=CITY, countrycode=COUNTRYCODE)

	weather = get_weather(location_string)

	if weather == {}:
		return(False)
		
	
 #----- Extract forecast data
 
	temperature = {}
	weather_icon = {}
	weekday = {}

	try:
		if "channel" in weather["query"]["results"]:
		
		 #----- Extract current weather data

			results = weather["query"]["results"]["channel"]
			current_temp = (int(results["item"]["condition"]["temp"]) - 32) * .5556
		
			current_datetime = results["item"]["condition"]["date"]
			tuple_date = email.utils.parsedate(current_datetime)
			current_H = time.strftime("%H", tuple_date)
			current_M = time.strftime("%M", tuple_date)
			if current_H == '12':
				if not ('PM' in str(current_datetime)):
					current_H = '00'
			elif 'PM' in str(current_datetime):
				current_H = str(int(current_H)+12)
			datetime = "%s:%s" %(current_H, current_M)			
			current_code = int(results["item"]["condition"]["code"])
			current_weather_icon = None
			for icon in icon_map:
				if current_code in icon_map[icon]:
					current_weather_icon = icon
					break

		#----- Extract weather forecast data

			for i in range(nb_forecast):
				temperature[i] = (int(results["item"]["forecast"][i]["high"]) - 32) * .5556
				day = results["item"]["forecast"][i]["day"]
				if (day in weekdays):
					if (COUNTRYCODE == 'FR'):
						weekday[i] = weekdays_FR[day]
					else:
						weekday[i] = weekdays[day]
				else:
					weekday[i] = "?"
				code = int(results["item"]["forecast"][i]["code"])
				weather_icon[i] = None
				for icon in icon_map:
					if code in icon_map[icon]:
						weather_icon[i] = icon
						break
		else:
			return(False)
	except:
		return(False)

#----- Load icon files and generate masks

	icons = {}
	masks = {}

	for icon in glob.glob("resources/icon-*.png"):
		icon_name = icon.split("icon-")[1].replace(".png", "")
		icon_image = Image.open(icon)
		icons[icon_name] = icon_image
		masks[icon_name] = inkyphat.create_mask(icon_image)

#----- Display current weather and forecast

#	inkyphat.set_border(inkyphat.BLACK)
	inkyphat.rectangle((0,31,212,104), white, white)

	#----- Display title
	
	inkyphat.rectangle((0,0,212,30), red, red)
	width, height = font20.getsize(location_string)
	d, r = divmod(width, 2)
	inkyphat.text((106-d, 3), location_string, white, font=font20)

	#----- Display current weather
	
	if current_weather_icon is not None:
		inkyphat.paste(icons[current_weather_icon], (8, 44), masks[current_weather_icon])
	else:
		inkyphat.text((16, 54), "?", inkyphat.RED, font=font20)

	inkyphat.text((14, 84), u"{:.0f}°".format(current_temp), red, font=font18)
	inkyphat.text((2, 32), datetime, black, font=font18)

	#----- Display weather forecast
	
	for i in range(nb_forecast):
		
		# Draw the current weather icon over the backdrop
		w_icon = weather_icon[i]
		if w_icon is not None:
			inkyphat.paste(icons[w_icon], (52 + i*38, 44), masks[w_icon])
		else:
			inkyphat.text((56 + i*38, 54), "?", inkyphat.RED, font=font20)

		inkyphat.text((60 + i*38, 84), u"{:.0f}°".format(temperature[i]), red, font=font18)
		inkyphat.text((60 + i*38, 32), weekday[i], black, font=font18)

	#----- Finish and display

	inkyphat.line((52, 30, 52, 104), black)
	inkyphat.show()
	
	return(True)


#-------------------------------------------------
#		Main function for shell command
#-------------------------------------------------


if __name__ == "__main__":
	arg = sys.argv
	
	if len(arg) == 1:
		try:
			location = get_location()
			city = location["city"]
			country = location["country"]
			if city == "" or country == "":
#				print("Can't get location, sorry")
				sys.exit(1)
			print("Fetching weather forecast for %s in %s" %(city, country))
		except:
			print("Can't get location, sorry")
			sys.exit(1)
	elif len(arg) == 2: 
		city = arg[1]
		country = 'FR'
	else:
		city = arg[1]
		country = arg[2]
		
	if rotate:
		inkyphat.set_rotation(180)

	ok = display_forecast(city, country)
	if ok:
		print("Weather forecast for %s in %s displayed ; enjoy !" %(city, country))
	else: 
		print("Couldn't display weather forecast for %s in %s ; sorry !" %(city, country))


#-------------------------------------------------
#----- END OF THE PROGRAMME ----------------------
#-------------------------------------------------
