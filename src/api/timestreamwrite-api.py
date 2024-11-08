import flask
from flask import request, Response
import subprocess

app = flask.Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "AWS TimeStream Writer is called via this endpoint"

@app.route('/api/v1/timestreamwrite', methods=['POST'])
def query():
    proc = f"python src/newtswriter.py"
    try:
        subprocess.run(proc, check=True)
    except subprocess.CalledProcessError as e:
        return Response(status=500)
    return Response(status=200)
if __name__ == '__main__':
    app.run(host="localhost", port=9678, debug=True)
