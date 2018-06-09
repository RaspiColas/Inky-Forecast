# Inky-Forecast

+--------------------------+
|   Inky Forecast project  |
+--------------------------+

Repository for inky_forecast project, including a python program for fetching on Yahoo server and displaying weather forecast on an Inky screen connected to a Raspberry Pi Zero

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
