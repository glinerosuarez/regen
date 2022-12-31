from datetime import timedelta, datetime

from airflow.decorators import dag, task

from extraction.klines import extract_klines

default_args = dict()


@dag(
    "extraction",
    default_args=default_args,
    description="Run tasks to extract data from external sources.",
    schedule=timedelta(days=1),
    start_date=datetime(2018, 1, 1),
    catchup=False,
    tags=["extraction"],
)
def extraction():
    extract_klines()


extraction()

