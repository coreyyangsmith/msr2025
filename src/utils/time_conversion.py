from datetime import datetime, timezone


def convert_datetime_to_timestamp_numbers(iso_timestamp):
    dt = datetime.strptime(iso_timestamp, "%Y-%m-%dT%H:%M:%SZ")
    dt = dt.replace(tzinfo=timezone.utc)
    epoch_millis = int(dt.timestamp() * 1000)
    return epoch_millis


def convert_timestamp_numbers_to_datetime(timestamp_ms):
    dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
    readable_date = dt.strftime("%Y-%m-%d %H:%M:%S %Z")
    return readable_date
