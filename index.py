from multiprocessing.pool import ThreadPool as Pool
from flask import Flask, request

from barentswatch_service import (
    get_ais,
    get_historic_positions_from_mmsi,
)
from helpers import distance
from mongo_service import (
    CouldNotDelete,
    DuplicateException,
    MMSINotFound,
    get_movements,
    insert_movement,
    remove_movement,
    update_movement,
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
            description=data.get("description"),
        )
    except DuplicateException:
        return "already exists", 400

    return "OK"


@app.route("/movements", methods=["GET"])
def movements():
    def process_movement(movement: dict):
        mmsi = movement["mmsi"]

        to_pos = (
            movement["to_position"]["lat"],
            movement["to_position"]["lng"],
        )
        from_pos = (
            movement["from_position"]["lat"],
            movement["from_position"]["lng"],
        )

        historic_positions = [*get_historic_positions_from_mmsi(mmsi)]
        current_pos = historic_positions.pop(0)
        current_lat, current_lng = current_pos

        movement["current_position"] = {"lat": current_lat, "lng": current_lng}
        movement["distance"] = distance(current_pos, to_pos)
        movement["max_distance"] = distance(from_pos, to_pos)
        movement["historic_positions"] = [
            {"lat": lat, "lng": lng} for lat, lng in historic_positions
        ]

        return movement

    with Pool(5) as p:
        return p.map(process_movement, get_movements())


@app.route("/movement/<mmsi>", methods=["DELETE"])
def delete_movement(mmsi: int):
    try:
        remove_movement(mmsi)
        return "OK"
    except CouldNotDelete:
        return f"Could not delete mmsi {mmsi}", 400


@app.route("/movements/<mmsi_str>", methods=["PATCH"])
def patch_movement(mmsi_str: str):
    if not mmsi_str.isnumeric():
        return "mmsi must be numeric", 400

    mmsi = int(mmsi_str)

    data = request.get_json()

    to_position = data.get("to_position")

    if to_position:
        if not isinstance(to_position, dict):
            return "to_position must be dict", 400

        if "lat" not in to_position or "lng" not in to_position:
            return "to_position must contain lat and lng"

        if not isinstance(to_position["lat"], float):
            return "lat must be float"

        if not isinstance(to_position["lng"], float):
            return "lng must be float"

    try:
        result = update_movement(
            mmsi=mmsi,
            to_position=to_position,
            description=data.get("description"),
        )

        return result
    except MMSINotFound:
        return "Could not find matching mmsi", 404


if __name__ == "__main__":
    app.run(debug=True, port=8000)
