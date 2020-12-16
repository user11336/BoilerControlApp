import datetime
import math
import re

import numpy as np

import consts


def round_timestamp(df):
    df[consts.TIMESTAMP_COLUMN_NAME] = df[consts.TIMESTAMP_COLUMN_NAME].apply(round_datetime)
    return df


def round_datetime(src_datetime):
    src_timestamp = src_datetime.timestamp()
    time_step_in_seconds = consts.TIME_TICK.total_seconds()
    rounded_timestamp = math.ceil(src_timestamp / time_step_in_seconds) * time_step_in_seconds
    rounded_datetime = datetime.datetime.fromtimestamp(rounded_timestamp, tz=src_datetime.tzinfo)
    return rounded_datetime


def interpolate_t(df, min_datetime=None, max_datetime=None, t_column_name=consts.FORWARD_PIPE_COLUMN_NAME):
    if min_datetime is not None:
        df = interpolate_first_t(df, min_datetime, t_column_name)
    if max_datetime is not None:
        df = interpolate_last_t(df, max_datetime, t_column_name)
    df = interpolate_passes_of_t(df, t_column_name)
    return df


def interpolate_first_t(df, min_datetime, t_column_name=consts.FORWARD_PIPE_COLUMN_NAME):
    min_datetime = round_datetime(min_datetime)

    first_datetime_idx = df[consts.TIMESTAMP_COLUMN_NAME].idxmin()
    first_row = df.loc[first_datetime_idx]
    first_t = first_row[t_column_name]
    first_datetime = first_row[consts.TIMESTAMP_COLUMN_NAME]
    if first_datetime > min_datetime:
        df = df.append(
            {consts.TIMESTAMP_COLUMN_NAME: min_datetime, t_column_name: first_t},
            ignore_index=True
        )
    return df


def interpolate_last_t(df, max_datetime, t_column_name=consts.FORWARD_PIPE_COLUMN_NAME):
    max_datetime = round_datetime(max_datetime)

    last_datetime_idx = df[consts.TIMESTAMP_COLUMN_NAME].idxmax()
    last_row = df.loc[last_datetime_idx]
    last_t = last_row[t_column_name]
    last_datetime = last_row[consts.TIMESTAMP_COLUMN_NAME]
    if last_datetime < max_datetime:
        df = df.append(
            {consts.TIMESTAMP_COLUMN_NAME: max_datetime, t_column_name: last_t},
            ignore_index=True
        )
    return df


def interpolate_passes_of_t(df, t_column_name=consts.FORWARD_PIPE_COLUMN_NAME):
    df = sort_by_timestamp(df)

    interpolated_values = []

    previous_datetime = None
    previous_t = None
    for index, row in df.iterrows():

        if previous_datetime is None:
            previous_datetime = row[consts.TIMESTAMP_COLUMN_NAME]
            previous_t = row[t_column_name]
            continue

        next_datetime = row[consts.TIMESTAMP_COLUMN_NAME]
        next_t = row[t_column_name]

        datetime_delta = next_datetime - previous_datetime
        if datetime_delta > consts.TIME_TICK:
            number_of_passes = int(datetime_delta // consts.TIME_TICK) - 1
            t_step = (next_t - previous_t) / number_of_passes
            for pass_n in range(1, number_of_passes + 1):
                interpolated_datetime = previous_datetime + (consts.TIME_TICK * pass_n)
                interpolated_t = previous_t + (t_step * pass_n)
                interpolated_values.append({
                    consts.TIMESTAMP_COLUMN_NAME: interpolated_datetime,
                    t_column_name: interpolated_t,
                })

        previous_t = next_t
        previous_datetime = next_datetime

    df = df.append(interpolated_values)
    df = sort_by_timestamp(df)

    return df


def sort_by_timestamp(df):
    df.sort_values(by=consts.TIMESTAMP_COLUMN_NAME, ignore_index=True, inplace=True)
    return df


def filter_by_timestamp(df, min_date, max_date):
    df = df[
        (df[consts.TIMESTAMP_COLUMN_NAME] >= min_date) &
        (df[consts.TIMESTAMP_COLUMN_NAME] < max_date)
        ]
    return df


# noinspection SpellCheckingInspection
def average_values(x, window_len=4, window='hanning'):
    if x.ndim != 1:
        raise ValueError("smooth only accepts 1 dimension arrays.")

    if x.size < window_len:
        raise ValueError("Input vector needs to be bigger than window size.")

    if window not in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError("Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")

    if window_len < 3:
        return x

    s = np.r_[x[window_len - 1:0:-1], x, x[-2:-window_len - 1:-1]]

    if window == 'flat':
        w = np.ones(window_len, 'd')
    else:
        w = getattr(np, window)(window_len)

    y = np.convolve(w / w.sum(), s, mode='valid')
    return y[(window_len // 2 - 1 + (window_len % 2)):-(window_len // 2)]
    # return y


def remove_duplicates_by_timestamp(df):
    df.drop_duplicates(consts.TIMESTAMP_COLUMN_NAME, inplace=True, ignore_index=True)
    return df


def reset_index(df):
    df.reset_index(drop=True, inplace=True)
    return df


def exclude_rows_without_value(df, column_name=consts.FORWARD_PIPE_COLUMN_NAME):
    df = df[df[column_name].notnull()]
    return df


def convert_to_float(df, column_name=consts.FORWARD_PIPE_COLUMN_NAME):
    df[column_name] = df[column_name].apply(convert_str_to_float)
    return df


def convert_str_to_float(value):
    if isinstance(value, str):
        value = value.replace(",", ".")
    value = float(value)
    return value


def remove_bad_zeros_in_water_t(df, column_name=consts.FORWARD_PIPE_COLUMN_NAME):
    df[column_name] = df[column_name].apply(lambda t: t > 100 and t / 100 or t)
    return df


def remove_disabled_t(df, disabled_t_threshold, column_name=consts.FORWARD_PIPE_COLUMN_NAME):
    if disabled_t_threshold != 0:
        df = df[df[column_name] >= disabled_t_threshold]
    return df


# noinspection SpellCheckingInspection
def convert_date_and_time_to_timestamp(df, tzinfo=None):
    datetime_list = []
    for _, row in df.iterrows():
        time_as_str = row[consts.SOFT_M_TIME_COLUMN_NAME]
        time = parse_time(time_as_str)

        date = row[consts.SOFT_M_DATE_COLUMN_NAME].date()

        datetime_ = datetime.datetime.combine(date, time, tzinfo=tzinfo)
        datetime_list.append(datetime_)

    df[consts.TIMESTAMP_COLUMN_NAME] = datetime_list
    del df[consts.SOFT_M_DATE_COLUMN_NAME]
    del df[consts.SOFT_M_TIME_COLUMN_NAME]

    return df


def parse_time(time_as_str):
    parsed = re.match(r"(?P<hour>\d\d):(?P<min>\d\d):(?P<sec>\d\d)", time_as_str)
    hour = int(parsed.group("hour"))
    minute = int(parsed.group("min"))
    second = int(parsed.group("sec"))
    time = datetime.time(hour=hour, minute=minute, second=second)
    return time


def rename_column(df, src_name, dst_name):
    df[dst_name] = df[src_name]
    del df[src_name]
    return df


def round_down(df, column_name=consts.FORWARD_PIPE_COLUMN_NAME):
    df[column_name] = df[column_name].apply(math.floor)
    return df


def convert_str_to_timestamp(df):
    df[consts.TIMESTAMP_COLUMN_NAME] = df[consts.TIMESTAMP_COLUMN_NAME].apply(parse_datetime)
    return df


def parse_datetime(datetime_as_str, datetime_patterns=consts.DATETIME_PATTERNS, timezone=None):
    for pattern in datetime_patterns:
        parsed = re.match(pattern, datetime_as_str)
        if parsed is not None:
            break
    else:
        raise ValueError("Date and time are not matched using existing patterns")

    year = int(parsed.group("year"))
    month = int(parsed.group("month"))
    day = int(parsed.group("day"))
    hour = int(parsed.group("hours"))
    minute = int(parsed.group("minutes"))
    second = 0
    millisecond = 0

    datetime_ = datetime.datetime(year, month, day, hour, minute, second, millisecond, tzinfo=timezone)
    return datetime_


def get_min_max_timestamp(df):
    if df.empty:
        return None, None

    min_date = df[consts.TIMESTAMP_COLUMN_NAME].min()
    max_date = df[consts.TIMESTAMP_COLUMN_NAME].max()
    return min_date, max_date