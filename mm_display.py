#!/usr/bin/env python
# -*- coding: utf-8 -*-

#---------------------------------------------------#
#													#
#				mm_display.py		        		#
#				by N.Mercouroff						#
#													#
#---------------------------------------------------#

version_prog = "200720"
name_prog = "mm_display.py"


"""
Version: 20/7/20

Python program for displaying information on a "magic mirror", ie, a 7 inch e-ink screen, connected to a Raspberry Pi Zero

Information displayed includes:
- local and global IP address and CPU info
- local weather and forecast for 7 days (from openweather  server)
- local tide hours (if relevant, grabbed from horaire-maree web server)
- current calendar

HISTORY:
--------
20/7/20:
- Cleanup of the code

24/9/19:
- Version adapted to What Pimoroni 400x300 eink screen

3/8/19:
- First development, derivated from inky_weather_tide.py project


USAGE:
-----
From the shell: displays local & global IP, and CPU information


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
- icon-hitide.png: Icon for high tide
- icon-surise.png: Icon for the sun rise
- icon-sunset.png: Icon for the sun set

Installation of the lib:
	curl https://get.pimoroni.com/inky | bash


SIDE EFFECTS:
------------


KNOWN BUGS:
----------

"""


#-------------------------------------------------
#--- IMPORTS -------------------------------------
#-------------------------------------------------


from glob import glob
from time import strftime
from font_source_serif_pro import SourceSerifProSemibold
# from font_source_sans_pro import SourceSansProSemibold
from os import path

from inky import InkyWHAT
from PIL import Image, ImageFont, ImageDraw


#-------------------------------------------------
#--- DEFINITIONS ---------------------------------
#-------------------------------------------------

PATH_PREFIX = path.dirname(path.abspath(__file__)) + '/'
LOG_FILENAME = PATH_PREFIX + "log_magicmirror.log"
ICON_SOURCE = PATH_PREFIX + "resources/icon-*.png"

ICON_MAPPING = {
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
	"50n": "myst",
	"60d": "wind",
	"rise": "sunrise",
	"set": "sunset",
	"hitide": "hitide",
	"lotide": "lowtide",
	"tidecoef": "tidecoef",
	"wind": "wind"
}

TIDENAME_FR = u'Marées :'
TIDENAME = u'Tides:'

FONT15 = ImageFont.truetype(SourceSerifProSemibold, 15)
FONT18 = ImageFont.truetype(SourceSerifProSemibold, 18)
FONT20 = ImageFont.truetype(SourceSerifProSemibold, 20)
FONT24 = ImageFont.truetype(SourceSerifProSemibold, 24)

EPD_WIDTH = 400  # 212  #
EPD_HEIGHT = 300  # 104  #
font_factor = 1

verbose = True

icons = {}

image = {}

NB_FORECASTS = 5  # Nb of days of forecast
NB_EVENTS = 2  # Nb of events to display

TEXT_OFFSET = 18

TITLE_RECT_R = 399
TITLE_RECT_B = 24
TITLE_TEXT_H = 200
TITLE_TEXT_V = 16

INFO_TEXT_H = 5
INFO_TEXT_LOCIP_V = 51
INFO_TEXT_PUBIP_V = 73
INFO_TEXT_CPU_V = 98

EPHEM_RECT_T = 28
EPHEM_RECT_R = 120
EPHEM_RECT_B = 49
EPHEM_TEXT_TITLE_H = 7
EPHEM_TEXT_TITLE_V = 43
EPHEM_ICON_RISE_H = 7
EPHEM_ICON_RISE_V = 50
EPHEM_TEXT_RISE_H = 57
EPHEM_TEXT_RISE_V = 75
EPHEM_ICON_SET_H = 7
EPHEM_ICON_SET_V = 85
EPHEM_TEXT_SET_H = 57
EPHEM_TEXT_SET_V = 101

WEA_ICON_COND_H = 30
WEA_ICON_COND_V = 135
WEA_TEXT_T_H = 22
WEA_TEXT_T_V = 197
WEA_TEXT_TEMP_H = 47
WEA_TEXT_TEMP_V = 197
WEA_ICON_WIND_H = 2
WEA_ICON_WIND_V = 197
WEA_TEXT_W_H = 47
WEA_TEXT_W_V = 218
WEA_TEXT_WIND_H = 72
WEA_TEXT_WIND_V = 220
WEA_TEXT_WINDDIR_H = 47
WEA_TEXT_WINDDIR_V = 239
WEA_RECT_T = 118
WEA_RECT_R = 120
WEA_RECT_B = 139
WEA_RECT_B2 = 197
WEA_TEXT6_H = 7
WEA_TEXT6_V = 133

FORCST_RECT1_L = 126
FORCST_RECT1_T = 28
FORCST_RECT1_R = 399
FORCST_RECT1_B = 49
FORCST_TEXT1_H = 155
FORCST_TEXT1_H_INCR = 55
FORCST_TEXT1_V = 43
FORCST_TEXT2_H = 155
FORCST_TEXT2_H_INCR = 55
FORCST_TEXT2_V = 197
FORCST_TEXT3_H = 155
FORCST_TEXT3_H_INCR = 55
FORCST_TEXT3_V = 218
FORCST_TEXT4_H = 155
FORCST_TEXT4_H_INCR = 55
FORCST_TEXT4_V = 239
FORCST_ICON1_H = 133
FORCST_ICON1_H_INCR = 55
FORCST_ICON1_V = 55
FORCST_ICON2_H = 133
FORCST_ICON2_H_INCR = 55
FORCST_ICON2_V = 95
FORCST_ICON3_H = 133
FORCST_ICON3_H_INCR = 55
FORCST_ICON3_V = 135
FORCST_LINE1_L = 181
FORCST_LINE1_L_INCR = 55
FORCST_LINE1_T = 28
FORCST_LINE1_R = 181
FORCST_LINE1_R_INCR = 55
FORCST_LINE1_B = 254
FORCST_LINE1_B2 = 212
FORCST_LINE2_L = 126
FORCST_LINE2_T = 28
FORCST_LINE2_R = 126
FORCST_LINE2_R_INCR = 55
FORCST_LINE2_B = 28

TIDE_RECT_T = 28
TIDE_RECT_R = 120
TIDE_RECT_B = 49
TIDE_TEXT1_H = 7
TIDE_TEXT1_V = 43
TIDE_ICON_L = 7
TIDE_ICON_R = 59
TIDE_TEXT2_H = 62
TIDE_TEXT2_V = 70
TIDE_TEXT3_H = 62
TIDE_TEXT3_V = 91
TIDE_TEXT4_H = 7
TIDE_TEXT4_V = 112
TIDE_TEXT5_H = 62
TIDE_TEXT5_V = 112

CAL_TEXT_L = 7
CAL_TEXT_R = 275
CAL_TEXT_R2 = 233
CAL_TEXT_R_INCR = 21

INIT_RECT1_T = 28
INIT_RECT1_R = 120
INIT_RECT1_B = 254
INIT_RECT1_B2 = 212
INIT_RECT2_L = 126
INIT_RECT2_T = 28
INIT_RECT2_R = 399
INIT_RECT2_B = 254
INIT_RECT2_B2 = 212


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
		Saves information to logfile, and prints it if verbose or forceprint is on
	"""
	txt = remove_non_ascii(txt)
	if verbose or forceprint:
		print(txt)
	now = strftime('%Y/%m/%d %H:%M:%S')
	msg = "%s\t%s" % (now, txt)
	with open(LOG_FILENAME, 'a') as file:
		file.write(msg + "\n")
	return

#-------------------------------------------------
#		Display functions
#-------------------------------------------------

def get_font15():
	return FONT15


def draw_init(rotate):
	global icons
	global image, inky_screen, draw

	tolog("Initialising the screen...")

	for icon in glob(ICON_SOURCE):
		icon_name = icon.split("icon-")[1].replace(".png", "")
		icon_image = Image.open(icon)
		icons[icon_name] = icon_image

	inky_screen = InkyWHAT('black')
	image = Image.new('P', (EPD_WIDTH, EPD_HEIGHT))
	draw = ImageDraw.Draw(image)

	tolog("...inky screen initialised")
	return True


def clear_display():

	draw_rect(0, 0, EPD_WIDTH, EPD_HEIGHT, False)
	return


def draw_line(x1, y1, x2, y2):
	global draw

	draw.line([x1, y1, x2, y2], fill=inky_screen.BLACK, width=1)
	return


def draw_cicle(x, y, r, fill_color):
	global draw

	draw.ellipse([x-r, y-r, x+r, y+r], fill=inky_screen.BLACK, outline=0)
	return


def draw_rect(x1, y1, x2, y2, fill = False):
	global draw

	if fill:
		draw.rectangle([x1, y1, x2, y2], fill=inky_screen.BLACK, outline=inky_screen.BLACK)
	else:
		draw.rectangle([x1, y1, x2, y2], fill=inky_screen.WHITE, outline=inky_screen.BLACK)
	return


def draw_text(x1, y1, text, inverse=False, font=FONT20):
	global draw

	if inverse:
		draw.text([x1, y1 - TEXT_OFFSET], text, fill=inky_screen.WHITE, font=font)
	else:
		draw.text([x1, y1 - TEXT_OFFSET], text, fill=inky_screen.BLACK, font=font)
	return


def draw_text_center(x, y, text, inverse=False, font=FONT20):
	global draw

	width = draw.textsize(text, font=font)[0]
	if inverse:
		draw.text([x - width / 2, y - TEXT_OFFSET], text, fill=inky_screen.WHITE, font=font)
	else:
		draw.text([x - width / 2, y - TEXT_OFFSET], text, fill=inky_screen.BLACK, font=font)
	return True


def draw_icon(x, y, code):
	global image, draw

	tolog("Drawing icon...")
	if code in ICON_MAPPING:
		icon_current = ICON_MAPPING[code]
		tolog("...icon %s displayed" % (icon_current))
		image.paste(icons[icon_current], (x, y))
	else:
		tolog("...no icon found", True)
		draw_text(x+8, y+10, '?')
	return


def draw_image(x, y, image_name):
	global image, draw

	tolog("Drawing image %s..." %(image_name))
	try:
		image_draw = Image.open(image_name)

		# basewidth = 300
		# wpercent = (basewidth/float(iimagemg.size[0]))
		# hsize = int((float(img.size[1])*float(wpercent)))
		image.paste(image_draw.resize((320, 240)), (x, y))
	except Exception as e:
		tolog("...error displaying image: %s" % (e), True)
	return



def display_show():
	global image, inky_screen

	tolog("Finishing display...")
	inky_screen.set_image(image)
	inky_screen.show()
	tolog("...display finished")

	return True


#-------------------------------------------------
#		Display title
#-------------------------------------------------

def display_title(text):
	"""
		Displays the ephemeris data on inky display
	"""
	draw_rect(0, 0, TITLE_RECT_R, TITLE_RECT_B, False)
	draw_text_center(TITLE_TEXT_H, TITLE_TEXT_V, text)

	return True


#-------------------------------------------------
#		Display information
#-------------------------------------------------

def display_IP(city, local_IP, public_IP, info_CPU):
	"""
		Displays the IP and CPU data on inky display
	"""
	title = "%s %s" % (city, strftime('%d/%m %H:%M'))

	display_title(title)

	draw_text(INFO_TEXT_H, INFO_TEXT_LOCIP_V, local_IP, False, FONT18)
	draw_text(INFO_TEXT_H, INFO_TEXT_PUBIP_V, public_IP, False, FONT18)
	draw_text(INFO_TEXT_H, INFO_TEXT_CPU_V, info_CPU, False, FONT18)

	return local_IP, public_IP, info_CPU


#-------------------------------------------------
#		Main function to display forecast
#-------------------------------------------------

def display_ephem(weather_data, country = 'Fr'):
	"""
		Displays the ephemeris data on inky display
	"""
	try:
		tolog("Displaying ephemeris (Rising = %s, Setting = %s)..." % (weather_data['sunrise'], weather_data['sunset']))

		if country == 'Fr':
			sun_name = u'Soleil :'
		else:
			sun_name = u'Sun:'

		draw_rect(0, EPHEM_RECT_T, EPHEM_RECT_R, EPHEM_RECT_B, True) 
		draw_text(EPHEM_TEXT_TITLE_H, EPHEM_TEXT_TITLE_V, sun_name, True, FONT20)
		draw_icon(EPHEM_ICON_RISE_H, EPHEM_ICON_RISE_V, 'rise')
		draw_text(EPHEM_TEXT_RISE_H, EPHEM_TEXT_RISE_V, '%s' %(weather_data['sunrise']), False, FONT18)  
		draw_icon(EPHEM_ICON_SET_H, EPHEM_ICON_SET_V, 'set')
		draw_text(EPHEM_TEXT_SET_H, EPHEM_TEXT_SET_V, '%s' %(weather_data['sunset']), False, FONT18)  
		tolog("...display of ephemeris ok")
		return True
	except Exception as e:
		tolog("...error displaying ephemeris: %s" % (e), True)
		return False

def display_weather(weather_data, wind_display):
	"""
		Displays the weather data on inky display
	"""
	tolog("Displaying current weather (Temp = %s, Time = %s, Cond = %s)..." % (weather_data['temp'], weather_data['time'], weather_data['condition_name']))

	try:

		draw_icon(WEA_ICON_COND_H, WEA_ICON_COND_V, weather_data['condition_code']) 
		draw_text(WEA_TEXT_T_H, WEA_TEXT_T_V, u"T°", False, FONT18) 
		draw_text(WEA_TEXT_TEMP_H, WEA_TEXT_TEMP_V, u"{:.0f}°C".format(weather_data['temp']), False, FONT18) 

		if wind_display:
			windir = weather_data['wind_dir']
			draw_icon(WEA_ICON_WIND_H, WEA_ICON_WIND_V, "wind")
			draw_text(WEA_TEXT_W_H, WEA_TEXT_W_V, "{:.0f}".format(weather_data['wind']), False, FONT18) 
			draw_text(WEA_TEXT_WIND_H, WEA_TEXT_WIND_V, "km/h", False, FONT15) 
			if windir != '?':
				draw_text(WEA_TEXT_WINDDIR_H, WEA_TEXT_WINDDIR_V, "(%s)" %(windir), False, FONT18)  # 47, 233

		draw_rect(0, WEA_RECT_T, WEA_RECT_R, WEA_RECT_B, True) 

		draw_text(WEA_TEXT6_H, WEA_TEXT6_V, u'Météo :', True, FONT20) 
		tolog("...display of weather ok")
		return True
	except Exception as e:
		tolog("...error displaying weather: %s" % (e), True)
		return False


def display_forecast(forecast_data, wind_display):
	"""
		Displays the forecast data on inky display
	"""

	tolog("Displaying current weather...")
	try:
		draw_rect(FORCST_RECT1_L, FORCST_RECT1_T, FORCST_RECT1_R, FORCST_RECT1_B, True)	
		for day in range(NB_FORECASTS):
			daily_forecast = forecast_data[day]
			draw_text_center(FORCST_TEXT1_H + day * FORCST_TEXT1_H_INCR, FORCST_TEXT1_V, daily_forecast['nameday'], True, FONT18)
			draw_text_center(FORCST_TEXT2_H + day * FORCST_TEXT2_H_INCR, FORCST_TEXT2_V,
					u"{:.0f}/{:.0f}°".format(daily_forecast['temp_min'], daily_forecast['temp_max']), False, FONT18)	

			if wind_display:
				windir = daily_forecast['wind_max_dir']
				draw_text_center(FORCST_TEXT3_H + day * FORCST_TEXT3_H_INCR, FORCST_TEXT3_V,
						u"{:.0f}".format(daily_forecast['wind_max']), False, FONT18)	
				if windir != '?':
					draw_text_center(FORCST_TEXT4_H + day * FORCST_TEXT4_H_INCR, FORCST_TEXT4_V, "(%s)" % (windir), False, FONT18)	
				draw_line(FORCST_LINE1_L + day * FORCST_LINE1_L_INCR, FORCST_LINE1_T, FORCST_LINE1_R + day * FORCST_LINE1_R_INCR, FORCST_LINE1_B)  
			else:
				draw_line(FORCST_LINE1_L + day * FORCST_LINE1_L_INCR, FORCST_LINE1_T, FORCST_LINE1_R + day * FORCST_LINE1_R_INCR, FORCST_LINE1_B2)  
			
			for utc_time in daily_forecast['hours']:
				tolog("Day = %s, Time = %s" % (day, utc_time))
				if utc_time == '09':
					draw_icon(FORCST_ICON1_H + day * FORCST_ICON1_H_INCR, FORCST_ICON1_V,
							daily_forecast['hours'][utc_time]['condition_code'])
				if utc_time == '12':
					draw_icon(FORCST_ICON2_H + day * FORCST_ICON2_H_INCR, FORCST_ICON2_V,
										daily_forecast['hours'][utc_time]['condition_code']) 
				if utc_time == '18':
					draw_icon(FORCST_ICON3_H + day * FORCST_ICON3_H_INCR, FORCST_ICON3_V,
										daily_forecast['hours'][utc_time]['condition_code'])

		if wind_display:
			draw_line(FORCST_LINE2_L, FORCST_LINE2_T, FORCST_LINE2_R + NB_FORECASTS + FORCST_LINE2_R_INCR, FORCST_LINE2_B)
		else:
			draw_line(FORCST_LINE2_L, FORCST_LINE2_T, FORCST_LINE2_R + NB_FORECASTS + FORCST_LINE2_R_INCR, FORCST_LINE2_B)
		tolog("...displaying ok")
		return True

	except Exception as e:
		tolog("...error displaying ephemeris: %s" % (e), True)
		return False


#-------------------------------------------------
#		Main function to display tide
#-------------------------------------------------

def display_tide(tide_hours, tide_coef, country):
	"""
		Displays the tide info on inky display
	"""

	tolog("Displaying current tide (hours: %s, %s, Coeff: %s)..." % (tide_hours[0], tide_hours[1], tide_coef))
	try:

		#----- Display tide info

		if country == 'Fr':
			# high_tide = "PM"
			tide_name = TIDENAME_FR
		else:
			# high_tide = "Hi"
			tide_name = TIDENAME

		draw_rect(0, TIDE_RECT_T, TIDE_RECT_R, TIDE_RECT_B , True)
		draw_text(TIDE_TEXT1_H, TIDE_TEXT1_V, tide_name, True, FONT20)
		draw_icon(TIDE_ICON_L, TIDE_ICON_R, 'hitide')
		if len(tide_hours) > 0:
			# draw_text(7, 28 + 2 * 21, '%s 1' %(high_tide), False, FONT18)
			draw_text(TIDE_TEXT2_H, TIDE_TEXT2_V, '%s' %(tide_hours[0]), False, FONT18)
		if len(tide_hours) > 1:
			# draw_text(7, 28 + 3 * 21, '%s 2' %(high_tide), False, FONT18)
			draw_text(TIDE_TEXT3_H, TIDE_TEXT3_V, '%s' %(tide_hours[1]), False, FONT18)
		draw_text(TIDE_TEXT4_H, TIDE_TEXT4_V, 'Coef', False, FONT18)
		# draw_icon(7, 28 + 5 * 21 / 2, 'tidecoef')
		draw_text(TIDE_TEXT5_H, TIDE_TEXT5_V, '%s' % (tide_coef), False, FONT18)
		tolog("...displaying ok")
		return True
	except Exception as e:
		tolog("...error displaying tides: %s" % (e), True)
		return False


#-------------------------------------------------
#		Main function to display calendar
#-------------------------------------------------

def display_calendar(month_cal, day_list, monthname, today, event_list, wind_display):
	"""
		Displays the calendar info on inky display
	"""

	tolog("Displaying Google calendar...")
	try:
		if len(event_list) != 0:
			if wind_display:
				nb_events = 2
			else:
				nb_events = 4
			max_events = min(nb_events, len(event_list))
			# if iss_inview :
			# 	max_events -= 1
			for i in range(max_events):
				if event_list[i]['time'] == '':
					event_summary = "%s : %s" % (event_list[i]['date'], event_list[i]['summary'])
				else:
					event_summary = "%s, %s : %s" % (event_list[i]['date'], event_list[i]['time'][:-3], event_list[i]['summary'])
				if wind_display:
					draw_text(CAL_TEXT_L, CAL_TEXT_R + i * CAL_TEXT_R_INCR, event_summary, False, FONT18)
				else:
					draw_text(CAL_TEXT_L, CAL_TEXT_R2 + i * CAL_TEXT_R_INCR, event_summary, False, FONT18)
		tolog("...displaying ok")
		return True
	except Exception as e:
		tolog("...error displaying calendar: %s" % (e), True)
		return False


#-------------------------------------------------
#		Main function to initiate tide & weather display
#-------------------------------------------------

def init_display(wind_display):
	clear_display()
	if wind_display:
		draw_rect(0, INIT_RECT1_T, INIT_RECT1_R, INIT_RECT1_B, False)
		draw_rect(INIT_RECT2_L, INIT_RECT2_T, INIT_RECT2_R, INIT_RECT2_B, False)
	else:
		draw_rect(0, INIT_RECT1_T, INIT_RECT1_R, INIT_RECT1_B2, False)
		draw_rect(INIT_RECT2_L, INIT_RECT2_T, INIT_RECT2_R, INIT_RECT2_B2, False)

	return True


#-------------------------------------------------
#		Main
#-------------------------------------------------

if __name__ == "__main__":
	tolog("Weather display started")

	draw_init(True)
	init_display(False)
	display_show()

	tolog("Informations displayed ; enjoy !")


#-------------------------------------------------
#----- END OF THE PROGRAMME ----------------------
#-------------------------------------------------
