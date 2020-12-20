
from datetime import datetime

from dataset_utils import data_consts
from boiler_control.weather_service.simple_weather_service import SimpleWeatherService


if __name__ == '__main__':

    t_provider = SimpleWeatherService()

    min_date = datetime.now()
    max_date = min_date + (data_consts.TIME_TICK * 10)
    a = t_provider.get_weather(min_date, max_date)
    print(a)
