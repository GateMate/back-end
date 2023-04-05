import asyncio
import requests


def requestWeather(latitude, longitude):
    locationArg = 'latitude='+str(latitude) + '&' + 'longitude='+str(longitude)
    hourlyArg = '&hourly=' + 'precipitation'
    numberOfDaysArg = '&forecast_days=' + str(3) #I'm pretty sure it includes the current day also starting at 0:00 o'clock
    #r = requests.get('https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&hourly=temperature_2m&current_weather=true', auth=('user','pass'))
    r = requests.get('https://api.open-meteo.com/v1/forecast?'+locationArg+hourlyArg+numberOfDaysArg, auth=('user','pass'))
    data = r.json()
    #print(data.keys())
    return r.json()
    #print(r.json())