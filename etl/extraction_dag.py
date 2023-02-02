from datetime import timedelta

import pendulum
from airflow.decorators import dag

from extraction.kline_minutes import extract_kline_minutes
from transform.insert_new_ma import insert_ma

default_args = dict(execution_timeout=timedelta(hours=1), retries=3, retry_delay=timedelta(minutes=2))


@dag(
    "extraction",
    default_args=default_args,
    description="Run tasks to extract data from external sources.",
    schedule=timedelta(minutes=1),
    start_date=pendulum.datetime(2023, 1, 28, 8, tz="UTC"),
    max_active_runs=1,
    catchup=True,
    tags=["extraction"],
)
def extraction():
    kline_id = extract_kline_minutes()
    insert_ma(kline_id)


extraction()
