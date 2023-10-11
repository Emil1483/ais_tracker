from flask import Flask, request

from barentswatch_service import get_ais

app = Flask(__name__)


@app.route("/")
def home():
    return "Hello World"


@app.route("/mmsi-search")
def mmsi_search():
    mmsi = request.args.get("mmsi")
    return get_ais(mmsi)


if __name__ == "__main__":
    app.run(debug=True, port=3000)
