#!/usr/bin/python
# -*- coding: utf-8 -*-

#---------------------------------------------------#
#													#
#				panic.py							#
#													#
#---------------------------------------------------#

""" 
Usage:

test_panic(test_loop = True):  
	Purpose: Tests the status of the monitoring and starts the monitoring of current process
	Returns: ok, diagnostic, with
		ok = True if there was no monitoring or if the monitored process is not running
		ok = False if the monitored process exists and is running
		ok = False if test_loop is True and the reboot is performed less than MIN_DELTA_SEC after previous test
		diagnostic = explanation of the status

delete_panic():
	Purpose: Removes the monitoring of the process
	Returns: ok, diagnostic, with
		ok = True if there was a monitoring and it was stopped
		diagnostic = explanation of the status

stop_process()
	Purpose: Kills the monitored process 
	Returns: ok, diagnostic, with
		ok = True if there was a monitoring and the monitored process has been killed successfully 
		ok = False if there is no monitoring, or if the monitored process is not running
		ok = False if the monitored process cannot be killed after MAX_ATTEMTS
		diagnostic = explanation of the status

"""

from os import path, getpid, remove, system
from time import time, sleep
import psutil

PATH_PREFIX = path.dirname(path.abspath(__file__)) + '/'
PANIC_FILENAME = PATH_PREFIX + 'panic.txt'
MIN_DELTA_SEC = 300  # Delay between reboot
MAX_ATTEMPTS = 10	# Waiting time in s for stopping process

OK_STOP_MSG = "OK: Program was not running and is now relaunched"
ERROR_RUNNING_MSG = "ERROR: Program already up and running"
ERROR_LOOP_MSG = "ERROR: Reboot loop"
ERROR_CRASH_MSG = "WARNING: Program has crashed and is now relaunched"
ERROR_NO_FILE = "No file"
ERROR_INIT = "ERROR initiating panic: %s"
ERROR_READING = "ERROR reading panic: %s"
ERROR_DELETING = "ERROR deleting panic: %s"
ERROR_MISSING_FILE = "ERROR: panic file not present"
ERROR_STOPPED_PROC = "ERROR: process %s already stopped"
ERROR_CANNOT_STOP_PROC = "ERROR: Cannot stop process %s after %s attemps"
ERROR_STOPPING_PROC = "ERROR stopping process %s: %s"



def init_panic():
	"""
		Saves the panic file, with the current time and process id
	"""

	err = ""
	try:
		with open(PANIC_FILENAME, "w") as bootdata_file:
			bootdata_file.write("%s\t%s" % (time(), str(getpid())))
	except Exception as e:
		err = ERROR_INIT % (e)
	return err


#---- Lecture des données dans le fichier de gestion de panic

def read_panic():
	"""
		Tests if panic file exists
		If yes, returns its data
	"""

	try:
		if not path.isfile(PANIC_FILENAME):
			return (ERROR_NO_FILE, 0, 0)

		with open(PANIC_FILENAME, "r") as bootdata_file:
			split_data = str(bootdata_file.read()).split('\t')

		return ("", float(split_data[0]), int(split_data[1]))
	except Exception as e:
		err = ERROR_READING % (e)
		return (err, 0, 0)


#---- Test si le raspberry est dans une boucle de reboot (mode panic)

def test_panic(test_loop = True):
	"""
		Tests if a panic file exists
		Returns True and the diagnostic if it does not exist or the process is not running
		Returns False and the diagnostic if the panic file exists and the process is running
		or if the reboot is performed too quickly
	"""

	err, boot_time_old, pid_old = read_panic()

	if err == ERROR_NO_FILE:			# If panic file not yet existing...
		err = init_panic()				# ...create it
		if err == '':
			return(True, OK_STOP_MSG)	# OK: No process was existing
		else:
			return(False, err)			# Error initiating panic file

	if err != '':
		return(False, err)				# Error testing if panic file exists

	if psutil.pid_exists(pid_old):		# If process still existing...
		return(False, ERROR_RUNNING_MSG)	# ...attempt to launch twice the program

	err = init_panic()
	if err != '':						# If error initiating panic file
		return(False, err)

	delta_boot = time() - boot_time_old
	if (delta_boot < MIN_DELTA_SEC) and test_loop:
		return(False, ERROR_LOOP_MSG)	# ...loop in reboot

	return(True, ERROR_CRASH_MSG)		# ...crash pre-existing



#---- Effacement du fichier de contrôle de panic

def delete_panic():
	"""
		Removes panic file
	"""
	try:
		remove(PANIC_FILENAME)
		return(True, "")
	except Exception as e:
		err = ERROR_DELETING % (e)
		return (False, err)

#---- Arrête du process

def stop_process():
	
	err, boot_time, pid = read_panic()

	if err == ERROR_NO_FILE:
		return False, ERROR_MISSING_FILE			# Error: No panic file existing

	if not psutil.pid_exists(pid):
		delete_panic()
		return False, ERROR_STOPPED_PROC % (pid)	# Error: Process not existing
	
	try:
		system('sudo kill -2 %s' % (pid))			# Killing the process
	
		i = 0
		while (psutil.pid_exists(pid)):
			sleep(1)
			i += 1
			if i > MAX_ATTEMPTS:
				return False, ERROR_CANNOT_STOP_PROC % (pid, MAX_ATTEMPTS)	# Process does not stop

		return True, ""

	except Exception as e:
		err = ERROR_STOPPING_PROC % (pid, e)
		return False, err						# Error killing the process
