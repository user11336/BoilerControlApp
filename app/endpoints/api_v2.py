import logging
from datetime import datetime
from typing import Optional

from dateutil.tz import gettz
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from containers import Services
from dataset_utils import data_consts
from services.boiler_t_predictor_service import BoilerTPredictorService

api_router = APIRouter(prefix="/api/v2")


@api_router.get("/getPredictedBoilerT", response_class=JSONResponse)
@inject
def get_predicted_boiler_t(
        start_datetime: Optional[datetime] = None,
        end_datetime: Optional[datetime] = None,
        timezone_name: Optional[str] = "Asia/Yekaterinburg",
        boiler_t_predictor: BoilerTPredictorService = Depends(Provide[Services.boiler_t_predictor_service])
):
    # noinspection SpellCheckingInspection
    """
        Метод для получения рекомендуемой температуры, которую необходимо выставить на бойлере.
        Принимает 3 **опциональных** параметра.
        - **start_datetime**: Дата время начала управляющего воздействия в формате ISO 8601
        См. https://en.wikipedia.org/wiki/ISO_8601.
        - **end_datetime**: Дата время окончания управляющего воздействия в формате ISO 8601.
        - **timezone_name**: Имя временной зоны для обработки запроса и генерации ответа.
        По-умолчанию берется из конфигов.
        См. столбец «TZ database name» https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List

        ---
        Формат времени в запросе:
        - YYYY-MM-DD?HH:MM[:SS[.fffffff]][+HH:MM] где ? это T или символ пробела.

        Примеры:
        - 2020-01-30 00:17:07+05:00 - Временная зона для парсинга берется из самой строки, предпочтительный вариант.
        - 2020-01-30 00:17+05 - Временная зона для парсинга берется из самой строки.
        - 2020-01-30 00:17+05:30 - Временная зона для парсинга берется из самой строки.
        - 2020-01-30 00:17 - Временная зона берется из параметра timezone_name.
        - 2020-01-30T00:17:01.1234567+05:00 - Временная зона для парсинга берется из самой строки, формат «O» в C#.

        ---
        Формат времени в ответе:
        - 2020-01-30T00:17:07+05:00 - Парсится при помощи DateTimeStyle.RoundtripKind в C#.
        Временна зона при формировании ответа берётся из парметра timezone_name. По-умолчанию берется из конфигов.
        """

    logging.debug(f"(API V2) Requested predicted boiler t for dates range "
                  f"from {start_datetime} to {end_datetime} timezone={timezone_name}")

    boiler_control_timezone = gettz(timezone_name)

    if start_datetime is None:
        start_datetime = datetime.now(tz=boiler_control_timezone)
    if start_datetime.tzname() is None:
        start_datetime = start_datetime.astimezone(boiler_control_timezone)

    if end_datetime is None:
        end_datetime = start_datetime + data_consts.TIME_TICK
    if end_datetime.tzname() is None:
        end_datetime = end_datetime.astimezone(boiler_control_timezone)

    predicted_boiler_t_df = boiler_t_predictor.get_need_boiler_t(start_datetime, end_datetime)

    predicted_boiler_t_ds = []
    for _, row in predicted_boiler_t_df.iterrows():
        datetime_ = row[data_consts.TIMESTAMP_COLUMN_NAME]
        datetime_ = datetime_.astimezone(boiler_control_timezone)

        boiler_t = row[data_consts.BOILER_NAME_COLUMN_NAME]
        boiler_t = round(boiler_t, 1)

        predicted_boiler_t_ds.append((datetime_, boiler_t))

    return predicted_boiler_t_ds