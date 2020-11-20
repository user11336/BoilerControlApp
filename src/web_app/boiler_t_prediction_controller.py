
from datetime import datetime

from flask import jsonify, request

import config
import consts
from dependency_injection import get_dependency
from datasets_utils.preprocess_utils import parse_datetime

from boiler_t_prediction.automated_boiler_t_predictor import AutomatedBoilerTPredictor


class BoilerTPredictionController:

    def __init__(self):
        self._automated_boiler_t_predictor: AutomatedBoilerTPredictor = get_dependency(AutomatedBoilerTPredictor)
        self._url_routes = [
            (self._get_predicted_boiler_t, "/api/v1/getPredictedBoilerT")
        ]

    def connect_methods_to_app(self, app):
        for method, rule in self._url_routes:
            app.add_url_rule(rule, view_func=method)

    def _get_predicted_boiler_t(self):
        start_date = request.args.get("start_date")
        if start_date is None:
            start_date = datetime.now()
        else:
            start_date = parse_datetime(start_date, config.DATETIME_PATTERNS)

        end_date = request.args.get("end_date")
        if end_date is None:
            end_date = start_date + consts.TIME_STEP
        else:
            end_date = parse_datetime(end_date, config.DATETIME_PATTERNS)

        predicted_boiler_t_df = self._automated_boiler_t_predictor.get_boiler_t(start_date, end_date)
        predicted_boiler_t_arr = predicted_boiler_t_df[consts.BOILER_NAME_COLUMN_NAME].to_list()
        predicted_boiler_t_dates_arr = predicted_boiler_t_df[consts.TIMESTAMP_COLUMN_NAME].to_list()

        predicted_boiler_t_ds = []
        for datetime_, boiler_t in zip(predicted_boiler_t_dates_arr, predicted_boiler_t_arr):
            datetime_as_str = datetime_.strftime("%Y-%m-%d %H:%M:%S")
            boiler_t = round(boiler_t, 1)
            predicted_boiler_t_ds.append((datetime_as_str, boiler_t))

        boiler_t_ds_json = jsonify(predicted_boiler_t_ds)
        return boiler_t_ds_json
