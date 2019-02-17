# Inky-Forecast

+--------------------------+
|   Inky Forecast project  |
+--------------------------+

Repository for inky_forecast project, including python programs for fetching weather and forecast info on Open Weather server and tide info on horaire-mareee.fr web server, and displaying the information on an Inky screen connected to a Raspberry Pi Zero

USAGE:
-----
From the shell: 

``python inky_weather_tide.py [-city city [countrycode]] [-h] [-v] [-tidename Name] [-weathername Name] [-tide] [-p]```

with:

	`-h`: Display help info

	`-v: Verbose mode

	`-p`: Print only mode (no display on Inky)

	`-info`: Display screen with IP info before weather

	`-tide`: Display daily tide info in place of current weather

	`-tidename`: Name to be used when fetching tide info (if different from city)

	`-weathername`: Name to be used when fetching weather info (if different from city)

	`-city city [countrycode]`: Name (and countrycode) to be used for title, tide and weather, unless stated otherwise for weather or tide (defaut is `CITY_DEFAULT, COUNTRY_DEFAULT`)

From another python program: 

```inky_weather_tide.inky_weather_tide(city, country, info_display=False, tide_display=False, rotate=True, tidename='', weathername='')```

Where:

	- `city` : name of the city where forcast shall be displayed (default is either local weather, as determined by IP, or `CITY_DEFAULT`)

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
- `icon-sun.png$ : sunny
- `icon-clear_nite.png`: clear night
- `icon-wind.png`: windy
- `icon-myst.png`: Fog


SIDE EFFECTS:
------------
Logs to LOG_FILENAME result (or error) of the program and displays it if verbose mode


KNOWN BUGS:
----------
- Sometimes `get_location` returns '' as location, and hence the forecast displayed is for `CITY_DEFAULT`
- `TIDE_URL` works only for some cities on the French West coast and returns no data if the city is not recognised (and sometimes the name should be CAPITALIZED) -- hence the option to force a city name with `-tidename` (list of cities here: `http://www.horaire-maree.fr/`)
- OPENWEATHER server works only for some cities and returns no data if the city is not recognised -- hence the option to force a city name with `-weathername` (list of cities is here: `http://bulk.openweathermap.org/sample/city.list.json.gz`)
