from datetime import timedelta

import pendulum
from airflow.decorators import dag

from extraction.klines import extract_klines
from transform.dbt_run import dbt_run

default_args = dict(execution_timeout=timedelta(hours=1), retries=3, retry_delay=timedelta(minutes=2))
backfill_end_date = pendulum.datetime(2023, 2, 2, 3, tz="UTC").end_of("hour")


@dag(
    "klines_backfill",
    default_args=default_args,
    description="Run tasks to backfill data from external sources.",
    schedule=timedelta(hours=16),
    start_date=pendulum.datetime(2022, 10, 24, tz="UTC"),
    end_date=backfill_end_date,
    catchup=True,
    tags=["backfill"],
)
def backfill():
    extract_klines()


@dag(
    "dbt_run",
    default_args=default_args,
    description="Run dbt for the first time.",
    start_date=backfill_end_date,
    tags=["backfill"],
)
def dbt_run_dag():
    dbt_run()


backfill()
dbt_run_dag()
