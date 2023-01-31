import subprocess
from flask import Flask, jsonify

app = Flask("dbt")


@app.route("/run")
def run_command():
    result = subprocess.run(["dbt run"], shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return jsonify({"return_code": result.returncode, "stdout": result.stdout.decode(), "stderr": result.stderr.decode()})


if __name__ == "__main__":
    app.run(port=5000, host='0.0.0.0', debug=True)
