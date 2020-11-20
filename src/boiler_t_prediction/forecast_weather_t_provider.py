
from datetime import datetime

from datasets_utils import config
import consts
from datasets_utils.preprocess_utils import (
    rename_column,
    interpolate_t,
    remove_duplicates_by_timestamp,
    convert_date_and_time_to_timestamp,
    filter_by_timestamp,
    get_min_max_timestamp,
    round_timestamp,
    round_datetime
)

import pandas as pd
import requests


class ForecastWeatherTProvider:

    def __init__(self):
        self._forecast_weather_t_cache = pd.DataFrame()

    def get_forecast_weather_t(self, min_date, max_date):
        min_date = round_datetime(min_date)
        max_date = round_datetime(max_date)

        if self._is_requested_datetime_not_in_cache(max_date):
            self._update_cache_from_server()

        return self._get_from_cache(min_date, max_date)

    def _is_requested_datetime_not_in_cache(self, requested_datetime):
        _, max_cached_datetime = get_min_max_timestamp(self._forecast_weather_t_cache)
        if max_cached_datetime is None:
            return True
        if max_cached_datetime <= requested_datetime:
            return True
        return False

    def _update_cache_from_server(self):
        df = self._request_from_server()
        df = self._preprocess_weather_t(df)
        self._update_cache(df)

    # noinspection PyMethodMayBeStatic
    def _request_from_server(self):
        url = f"{config.REMOTE_HOST}/JSON/"
        # noinspection SpellCheckingInspection
        params = {
            "method": "getPrognozT"
        }
        response = requests.get(url, params=params)
        df = pd.read_json(response.text)

        return df

    # noinspection PyMethodMayBeStatic
    def _preprocess_weather_t(self, df):
        df = rename_column(df, consts.SOFT_M_WEATHER_T_COLUMN_NAME, consts.WEATHER_T_COLUMN_NAME)
        df = convert_date_and_time_to_timestamp(df)
        df = round_timestamp(df)
        min_datetime, max_datetime = get_min_max_timestamp(df)
        df = interpolate_t(df, min_datetime, max_datetime, t_column_name=consts.WEATHER_T_COLUMN_NAME)
        df = remove_duplicates_by_timestamp(df)
        return df

    def _update_cache(self, df):
        new_df = pd.concat(
            (self._forecast_weather_t_cache, df),
            ignore_index=True
        )
        new_df = remove_duplicates_by_timestamp(new_df)
        self._forecast_weather_t_cache = new_df

    def _get_from_cache(self, min_date, max_date):
        return filter_by_timestamp(self._forecast_weather_t_cache, min_date, max_date).copy()

    def compact_cache(self):
        datetime_now = round_datetime(datetime.now())
        old_values_condition = self._forecast_weather_t_cache[consts.TIMESTAMP_COLUMN_NAME] < datetime_now
        old_values_idx = self._forecast_weather_t_cache[old_values_condition].index
        self._forecast_weather_t_cache.drop(old_values_idx, inplace=True)
