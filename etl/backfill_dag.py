from datetime import timedelta

import pendulum
from airflow.decorators import dag

from extraction.klines import extract_klines
from transform.dbt_run import dbt_run
from transform.populate_mas import populate_mas

default_args = dict(execution_timeout=timedelta(hours=1), retries=3, retry_delay=timedelta(minutes=2))
backfill_end_date = pendulum.datetime(2023, 2, 2, 16, tz="UTC").end_of("hour")


@dag(
    "klines_backfill",
    default_args=default_args,
    description="Run tasks to backfill data from external sources.",
    schedule=timedelta(hours=16),
    start_date=pendulum.datetime(2019, 9, 19, 10, 1, tz="UTC").add(days=100),
    end_date=backfill_end_date,
    catchup=True,
    tags=["backfill"],
)
def backfill():
    extract_klines()


@dag(
    "ma_backfill",
    default_args=default_args,
    description="Compute historical moving averages.",
    schedule=None,
    tags=["backfill"],
)
def backfill_ma():
    populate_mas()


@dag(
    "dbt_run",
    default_args=default_args,
    description="Run dbt for the first time.",
    schedule=None,
    tags=["backfill"],
)
def dbt_run_dag():
    dbt_run()


backfill()
backfill_ma()
dbt_run_dag()
