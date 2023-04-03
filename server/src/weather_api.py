import asyncio
import requests

from open_meteo import OpenMeteo
from open_meteo.models import DailyParameters, HourlyParameters


def requestWeather(latitude, longitude):
    locationArg = 'latitude='+str(latitude) + '&' + 'longitude='+str(longitude)
    hourlyArg = '&hourly=' + 'precipitation'
    numberOfDaysArg = '&forecast_days=' + str(3) #I'm pretty sure it includes the current day also starting at 0:00 o'clock
    #r = requests.get('https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&hourly=temperature_2m&current_weather=true', auth=('user','pass'))
    r = requests.get('https://api.open-meteo.com/v1/forecast?'+locationArg+hourlyArg+numberOfDaysArg, auth=('user','pass'))
    print(r.json())