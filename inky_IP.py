#!/usr/bin/env python
# -*- coding: utf-8 -*-

#---------------------------------------------------#
#													#
#				inky_IP.py			            	#
#													#
#---------------------------------------------------#

"""
Version: 12/2/19

Python program for fetching weather forecast on Yahoo server and tide info on web server, and displaying it on an Inky screen connected to a Raspberry Pi Zero in Ouessant

HISTORY:
--------
12/2/19:
- Program development 

USAGE:
-----
From the shell: python inky_IP.py [-v][-p] with:
-v: Verbose mode
-p: Print the result on the terminal instead of the inky screen

As a lib: display_info(text[, rotate]) with
text: The text to be displayed as ttile
rotate (default is true): Rotate the screen

"""

#-------------------------------------------------
#--- IMPORTS -------------------------------------
#-------------------------------------------------


import time, sys, os
import socket
from psutil import cpu_percent

has_inky = True
try:
	import inkyphat
except:
	has_inky = False
	print("No inky")

#-------------------------------------------------
#--- DEFINITIONS ---------------------------------
#-------------------------------------------------

white = 0
black = 1
red = 2

rotate = True

PATH_FILENAME = '/home/pi/Inky/'
LOG_FILENAME = 'log_inky.log'

TITLE_DEFAULT = "Information"

verbose = False

#-------------------------------------------------
#--- FUNCTIONS -----------------------------------
#-------------------------------------------------


#-------------------------------------------------
#		Useful functions
#-------------------------------------------------

#---- Envoi des information vers le log

def tolog(txt):
	now = time.strftime('%Y/%m/%d %H:%M:%S')
	msg = "%s\t%s" % (now, txt)
	if verbose:
		print(msg)
	with open(PATH_FILENAME + LOG_FILENAME, 'a') as file:
		file.write(msg + "\n")
	return()


def decode_arg(argv):
	global verbose, has_inky

	tolog("Decoding arguments...")
	for n in range(1, len(argv)):
		arg = argv[n]
		if arg == '-v':  # Verbose
			verbose = True
			tolog("Verbose mode")
		elif arg == '-p':  # Print only
			has_inky = False
			tolog("No inky mode")
	return


#---- Utilitaire de lecture de la température CPU

def read_CPU_temp():
	CPU_temp = '/sys/class/thermal/thermal_zone0/temp'
	
	temp_file = open(CPU_temp, "r")
	data = str(temp_file.read())
	temp_file.close()
	return (float(data)/1000)


#---- Utilitaire de lecture de l'adresse IP locale

def read_local_ip():
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.connect(("8.8.8.8", 80))
		ip_num = sock.getsockname()[0]
		sock.close()
		return ip_num
	except Exception as e:
		return "(unkown)"


#---- Utilitaire de lecture de l'adresse IP globale

def read_public_ip():
	try:
		public_ip = os.system("curl icanhazip.com > ip.txt")
		ip_file = open('ip.txt', 'r')
		public_ip = str(ip_file.read())
		ip_file.close()
		return public_ip
	except Exception as e:
		return "(unkown)"


#-------------------------------------------------
#		Display functions
#-------------------------------------------------

	
def display_info(text, rotate = True):

	title = "%s %s" % (text, time.strftime('%d/%m %H:%M'))

	local_IP = "IP loc.: %s" % (read_local_ip())
	public_IP = "IP pub.: %s" % (read_public_ip())
	info_CPU = "CPU: T. {:2.0f} C, load {:2.0f} %".format(read_CPU_temp(), cpu_percent())

	if has_inky:
		inkyphat.clear()
		font18 = inkyphat.ImageFont.truetype(inkyphat.fonts.FredokaOne, 18)
		font20 = inkyphat.ImageFont.truetype(inkyphat.fonts.FredokaOne, 20)
		font24 = inkyphat.ImageFont.truetype(inkyphat.fonts.FredokaOne, 24)
		if rotate:
			inkyphat.set_rotation(180)

		inkyphat.rectangle((0, 0, 212, 30), red, red)
		width, height = font20.getsize(title)
		d, r = divmod(width, 2)
		inkyphat.text((106-d, 3), title, white, font=font20)
		inkyphat.rectangle((0, 31, 212, 104), white, white)

		inkyphat.text((5, 31), local_IP, black, font=font18)
		inkyphat.text((5, 53), public_IP, black, font=font18)
		inkyphat.text((5, 78), info_CPU, red, font=font18)
		inkyphat.show()
	else:
		print(title)
		print(local_IP)
		print(public_IP)
		print(temp_CPU)
	
	return local_IP, public_IP, info_CPU


#-------------------------------------------------
#		Main function for shell command
#-------------------------------------------------


if __name__ == "__main__":
	tolog("Weather display started")

	decode_arg(sys.argv)

	local_IP, public_IP, temp_CPU = display_info(TITLE_DEFAULT, rotate)

	tolog(local_IP)
	tolog(public_IP)
	tolog(temp_CPU)

	tolog("Informations displayed ; enjoy !")

#-------------------------------------------------
#----- END OF THE PROGRAMME ----------------------
#-------------------------------------------------
