import datetime

import dateutil.tz


def to_timestamp(input_date):
    if isinstance(input_date, datetime.datetime):
        return int((input_date - datetime.datetime(1970, 1, 1)).total_seconds() * 1000)
    elif isinstance(input_date, datetime.date):
        return int((input_date - datetime.date(1970, 1, 1)).total_seconds() * 1000)
    else:
        raise AttributeError('input_date is not date nor datetime instance')


def from_timestamp(timestamp_milliseconds):
    return datetime.datetime.utcfromtimestamp(timestamp_milliseconds / 1000.0)


def utc_to_cet(utc_time):
    utc = dateutil.tz.gettz('UTC')
    cet = dateutil.tz.gettz('CET')
    utc_time = utc_time.replace(tzinfo=utc)
    return utc_time.astimezone(cet)


def cet_to_utc(cet_time):
    utc = dateutil.tz.gettz('UTC')
    cet = dateutil.tz.gettz('CET')
    if cet_time.tzinfo != cet:
        cet_time = cet_time.replace(tzinfo=cet)
    return cet_time.astimezone(utc)
