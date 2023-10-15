from re import A
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from helpers import string_to_object_id
import os


class DuplicateException(Exception):
    pass


class CouldNotDelete(Exception):
    pass


class MMSINotFound(Exception):
    pass


load_dotenv()

client = MongoClient(os.getenv("MONGO_URL"))
db = client["ais_tracker"]
movements_collection = db["movements"]


def insert_movement(
    name: str, mmsi: int, from_pos: dict, to_pos: dict, description: str
):
    vessel_data = {
        "_id": string_to_object_id(str(mmsi)),
        "name": name,
        "mmsi": mmsi,
        "from_position": from_pos,
        "to_position": to_pos,
        "description": description,
    }

    try:
        movements_collection.insert_one(vessel_data)
    except DuplicateKeyError:
        raise DuplicateException()


def get_movements():
    def gen():
        for movement in movements_collection.find():
            movement["_id"] = str(movement.get("_id"))
            yield movement

    return [*gen()]


def remove_movement(mmsi: int):
    result = movements_collection.delete_one(
        {
            "_id": string_to_object_id(str(mmsi)),
        }
    )

    if not result.deleted_count:
        raise CouldNotDelete()


def update_movement(mmsi: int, to_position: dict, description: str):
    fields = {}

    if to_position:
        fields["to_position"] = to_position

    if description:
        fields["description"] = description

    result = movements_collection.update_one(
        {"_id": string_to_object_id(str(mmsi))},
        {"$set": fields},
    )

    if result.matched_count != 1:
        raise MMSINotFound()

    return fields
