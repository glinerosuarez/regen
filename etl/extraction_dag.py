from datetime import timedelta

import pendulum
from airflow.decorators import dag

from extraction.klines import extract_klines

default_args = dict(max_active_runs=1, execution_timeout=timedelta(hours=1), retries=3, retry_delay=timedelta(minutes=2))


@dag(
    "extraction",
    default_args=default_args,
    description="Run tasks to extract data from external sources.",
    schedule=timedelta(hours=16),
    start_date=pendulum.datetime(2023, 1, 5, tz="UTC"),
    catchup=True,
    tags=["extraction"],
)
def extraction():
    extract_klines()


extraction()
