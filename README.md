# Magic Mirror

+--------------------------+
|   Magic Mirror project   |
+--------------------------+

Written by N.Mercouroff
21/July/20

<<<<<<< HEAD
Repository for magicmirror project, including python programs for fetching weather and forecast info on Open Weather server, and tide info on horaire-mareee.fr web servers, and for displaying the information on an wHAT screen connected to a Raspberry Pi Zero.

More info: https://raspicolas.wordpress.com/2019/09/29/pi-based-info-center-for-the-family-kitchen/
=======
Repository for inky_forecast project, including python programs for fetching weather and forecast info on Open Weather server, and tide info on horaire-maree.fr web servers, and for displaying the information on an Inky screen connected to a Raspberry Pi Zero
>>>>>>> master

USAGE:
-----
From the shell: 

```
python magicmirror.py [-city city [countrycode]] [-h] [-v] [-tidename Name] [-weathername Name] [-tide] [-p]
```

with:

`-h`: Display help info
`-v`: Verbose mode
`-p`: Print only mode (no display on Inky)
`-info`: Display screen with IP info before weather
`-tide`: Display daily tide info in place of current weather
`-tidename`: Name to be used when fetching tide info (if different from city)
`-weathername`: Name to be used when fetching weather info (if different from city)
`-city city [countrycode]`: Name (and countrycode) to be used for title, tide and weather, unless stated otherwise for weather or tide (defaut is set in config file)

From another python program: 

```
magicmirror.magicmirror_main(
	city, country, 
	info_display=False, tide_display=False, 
	rotate=True, 
	tidename='', weathername=''
)
```

Where:

- `city` : name of the city where forcast shall be displayed (default is either local weather, as determined by IP, or by config file`)
- `country` : code of the country (default is `COUNTRY_DEFAULT`)
- `info_display` : display IP info before the weather info
- `tide_display` : display tide and forecast info instead of current weather and forecat info
- `rotate` : rotate 180° the display
- `tidename`: Name to be used when fetching tide info (if different from city)
- `weathername`: Name to be used when fetching weather info (if different from city)


PREREQUISITS:
------------
Requires in current directory a subdirectory /resources with icon PNG files:
- `icon-cloud.png`: cloudy
- `icon-part_cloud.png`: partly cloudy
- `icon-rain.png`: raining
- `icon-snow.png`: snowing
- `icon-storm.png`: thunderstorm
<<<<<<< HEAD
- `icon-sun.png` : sunny
=======
- `icon-sun.png`: sunny
>>>>>>> master
- `icon-clear_nite.png`: clear night
- `icon-wind.png`: windy
- `icon-myst.png`: Fog
- `icon-hitide.png`: Icon for high tide
- `icon-surise.png`: Icon for the sun rise
- `icon-sunset.png`: Icon for the sun set

Requires the following standard modules:
- `time, sys, datetime, os, configparser`

Requires the following sub-programs and files:
- `panic.py` : to prevent re-entering of the code
- `mm_data` : to fetch weather, tide and calendar information 
- `mm_display` : to display information on the inky HAT / wHAT
- `config_magicmirror.conf` : configuration data
- `token.pickle` : to store the user's access and refresh tokens for Google Calendar (regenerated)

Installation of the libs:
	`curl https://get.pimoroni.com/inky | bash`
	`pip install ConfigParser`

`config_magicmirror.conf` format:

```
[LOCATION]
cityDefault = ...
countryDefault = ...

[GOOGLEID]
clientID = ...
client_secret = ...

[OPENWEATHER]
openWeatherID = ...

[FLAGS]
tideDisplay = True
rotate = True
```

openWeatherID to be filled with ID fetched from https://openweathermap.org
Note: clientID and client_secret are not used, only token.pickle is used (see https://developers.google.com/calendar/quickstart/python for more info)


SIDE EFFECTS:
------------
Logs to LOG_FILENAME result (or error) of the program and displays it if verbose mode


KNOWN BUGS:
----------
- Sometimes `get_location` returns `''` as location, and hence the forecast displayed is for `CITY_DEFAULT`
- `TIDE_URL` works only for some cities on the French West coast and returns no data if the city is not recognised (and sometimes the name should be CAPITALIZED) -- hence the option to force a city name with `-tidename` (list of cities here: `http://www.horaire-maree.fr/`)
- OPENWEATHER server works only for some cities and returns no data if the city is not recognised -- hence the option to force a city name with `-weathername` (list of cities is here: `http://bulk.openweathermap.org/sample/city.list.json.gz`)
