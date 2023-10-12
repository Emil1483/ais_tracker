import os
from dotenv import load_dotenv
from flask import Flask, request
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from barentswatch_service import get_ais, get_position_from_mmsi
from helpers import string_to_object_id

app = Flask(__name__)

load_dotenv()

client = MongoClient(os.getenv("MONGO_URL"))
db = client["ais_tracker"]
movements_collection = db["movements"]


@app.route("/")
def home():
    return "Hello World"


@app.route("/mmsi-search", methods=["GET"])
def mmsi_search():
    mmsi = request.args.get("mmsi")
    return get_ais(mmsi)


@app.route("/tracked-vessels", methods=["POST"])
def tracked_vessels():
    data = request.get_json()

    if "mmsi" not in data or "to_position" not in data:
        return "missing fields", 400

    mmsi = data["mmsi"]

    if not isinstance(mmsi, int):
        return "MMSI must be number", 400

    from_lat, from_lng = get_position_from_mmsi(mmsi)
    from_position = {
        "lat": from_lat,
        "lng": from_lng,
    }

    to_position = data["to_position"]

    if not isinstance(to_position, dict):
        return "to_position must be dict", 400

    if "lat" not in to_position or "lng" not in to_position:
        return "to_position must contain lat and lng"

    if not isinstance(to_position["lat"], float):
        return "lat must be float"

    if not isinstance(to_position["lng"], float):
        return "lng must be float"

    vessel_data = {
        "_id": string_to_object_id(str(mmsi)),
        "mmsi": mmsi,
        "from_position": from_position,
        "to_position": to_position,
    }

    try:
        movements_collection.insert_one(vessel_data)
    except DuplicateKeyError:
        return "already exists", 400

    return "OK"


if __name__ == "__main__":
    app.run(debug=True, port=8000)
