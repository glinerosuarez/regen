import requests
from airflow.decorators import task


@task
def dbt_run() -> None:
    """
    #### Task for executing dbt run command.
    Run dbt.
    """
    DBT_ENDPOINT = "http://dbt:5000/run"
    response = requests.get(DBT_ENDPOINT)

    if response.json()["return_code"] != 0:
        raise ValueError(
            f"dbt run command failed. \nstdout:\n{response.json()['stdout']}\nstderr:\n{response.json()['stderr']}"
        )

    print(response.json()["stdout"])
