import os
import pickle

from dateutil.tz import gettz
from matplotlib import pyplot as plt
from datetime import datetime

from configs.app_config import GlobalAppConfig
import data_consts
from services.weather_service.simple_weather_service import SimpleWeatherService
from services.boiler_t_predictor_service.simple_boiler_t_predictor_service import SimpleBoilerTPredictorService
import pandas as pd


if __name__ == '__main__':
    app_config = GlobalAppConfig.load_app_config()

    min_date = datetime.now(tz=gettz(app_config.datetime_processing.boiler_controller_timezone))
    max_date = min_date + (100 * data_consts.TIME_TICK)

    with open(app_config.boiler_t_predictor.optimized_t_table_path, "rb") as f:
        optimized_t_table = pickle.load(f)
    temp_graph = pd.read_csv(os.path.abspath(app_config.boiler_t_predictor.t_graph_path))
    homes_time_deltas = pd.read_csv(app_config.boiler_t_predictor.homes_deltas_path)
    max_home_time_delta = homes_time_deltas[data_consts.TIME_DELTA_COLUMN_NAME].max()

    weather_forecast_provider = SimpleWeatherService()
    weather_forecast_provider.set_server_timezone(
        gettz(app_config.weather_forecast_provider.server_timezone))
    weather_forecast_provider.set_server_address(app_config.weather_forecast_provider.server_address)

    boiler_t_predictor = SimpleBoilerTPredictorService()
    boiler_t_predictor.set_optimized_t_table(optimized_t_table)
    boiler_t_predictor.set_temp_requirements_service(temp_graph)
    boiler_t_predictor.set_homes_time_deltas(homes_time_deltas)
    boiler_t_predictor.set_weather_forecast_service(weather_forecast_provider)

    predicted_boiler_t_df = boiler_t_predictor.get_need_boiler_t(min_date, max_date)
    predicted_boiler_t_arr = predicted_boiler_t_df[data_consts.BOILER_NAME_COLUMN_NAME].to_numpy()

    dates_arr = predicted_boiler_t_df[data_consts.TIMESTAMP_COLUMN_NAME].to_list()

    weather_t_df = weather_forecast_provider.get_weather(min_date, max_date)
    weather_t_arr = weather_t_df[data_consts.WEATHER_T_COLUMN_NAME].to_numpy()
    weather_t_arr = weather_t_arr[:len(predicted_boiler_t_arr)]

    for idx, row in predicted_boiler_t_df.iterrows():
        print(row[data_consts.TIMESTAMP_COLUMN_NAME], round(row[data_consts.BOILER_NAME_COLUMN_NAME], 1))

    plt.plot(dates_arr, predicted_boiler_t_arr, label="Predicted boiler t")
    plt.plot(dates_arr, weather_t_arr, label="Weather t")

    plt.legend()
    plt.show()
