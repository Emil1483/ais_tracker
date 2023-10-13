from flask import Flask, request

from barentswatch_service import get_ais, get_position_from_mmsi
from helpers import distance
from mongo_service import (
    CouldNotDelete,
    DuplicateException,
    get_movements,
    insert_movement,
    remove_movement,
)

app = Flask(__name__)


@app.route("/")
def home():
    return "Hello World"


@app.route("/mmsi-search", methods=["GET"])
def mmsi_search():
    mmsi = request.args.get("mmsi")
    return get_ais(mmsi)


@app.route("/add-movement", methods=["POST"])
def add_movement():
    data = request.get_json()

    if "mmsi" not in data or "to_position" not in data:
        return "missing fields", 400

    mmsi = data["mmsi"]

    if not isinstance(mmsi, int):
        return "MMSI must be number", 400

    ais_data = get_ais(mmsi)
    if len(ais_data) != 1:
        return "invalid MMSI", 400

    ais = ais_data[0]
    from_position = {
        "lat": ais["latitude"],
        "lng": ais["longitude"],
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

    try:
        insert_movement(
            mmsi=mmsi,
            name=ais["name"],
            from_pos=from_position,
            to_pos=to_position,
        )
    except DuplicateException:
        return "already exists", 400

    return "OK"


@app.route("/movements", methods=["GET"])
def movements():
    def gen():
        for movement in get_movements():
            mmsi = movement["mmsi"]
            current_pos = get_position_from_mmsi(mmsi)
            lat, lng = current_pos

            to_pos = (
                movement["to_position"]["lat"],
                movement["to_position"]["lng"],
            )
            from_pos = (
                movement["from_position"]["lat"],
                movement["from_position"]["lng"],
            )

            movement["current_position"] = {"lat": lat, "lng": lng}
            movement["distance"] = distance(current_pos, to_pos)
            movement["max_distance"] = distance(from_pos, to_pos)

            yield movement

    data = [*gen()]
    return data


@app.route("/movement/<mmsi>", methods=["DELETE"])
def delete_movement(mmsi: int):
    try:
        remove_movement(mmsi)
        return "OK"
    except CouldNotDelete:
        return f"Could not delete mmsi {mmsi}", 400


if __name__ == "__main__":
    app.run(debug=True, port=8000)
