from datetime import datetime, timedelta

default_args = {
    "owner": "Raymond",
    "start_date": datetime(2023, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 5,
    "retry_delay": timedelta(minutes=5)
}