import subprocess
from flask import Flask

app = Flask("dbt")


@app.route("/run")
def run():
    result = subprocess.run(["dbt run"], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {
        "return_code": result.returncode,
        "stdout": result.stdout.decode("utf-8"),
        "stderr": result.stderr.decode("utf-8"),
    }


@app.route("/run_exclude_staging")
def run_exclude_staging():
    result = subprocess.run(
        ["dbt run --exclude models/staging/*+"], shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    return {
        "return_code": result.returncode,
        "stdout": result.stdout.decode("utf-8"),
        "stderr": result.stderr.decode("utf-8"),
    }


if __name__ == "__main__":
    app.run(port=5000, host="0.0.0.0", debug=True)
