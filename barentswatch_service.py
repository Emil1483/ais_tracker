import requests
import os
from time import time
from dotenv import load_dotenv
from datetime import datetime, timedelta


access_token_cache = {
    "token": None,
    "created_at": 0,
}


def get_access_token():
    token_age = time() - access_token_cache["created_at"]
    if token_age < 3600:
        return access_token_cache["token"]

    load_dotenv()

    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    response = requests.post(
        "https://id.barentswatch.no/connect/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "ais",
            "grant_type": "client_credentials",
        },
    )

    access_token = response.json()["access_token"]

    access_token_cache["token"] = access_token
    access_token_cache["created_at"] = time()

    return access_token


def get_ais(mmsi: int):
    token = get_access_token()
    response = requests.post(
        "https://live.ais.barentswatch.no/v1/latest/combined",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "mmsi": [mmsi],
        },
    )

    results = response.json()

    return results


def get_position_from_mmsi(mmsi: int):
    results = get_ais(mmsi)

    if not results:
        return None

    data = results[0]

    lat = data["latitude"]
    lng = data["longitude"]
    return lat, lng


def search_for_vessel(query: str):
    token = get_access_token()
    response = requests.get(
        "https://historic.ais.barentswatch.no/open/v2/historic/search",
        params={"q": query},
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        },
    )

    return response.json()


def get_historic_ais(mmsi: int):
    token = get_access_token()

    from_date = datetime.now() - timedelta(hours=36)
    to_date = datetime.now()

    response = requests.get(
        f"https://historic.ais.barentswatch.no/open/v1/historic/tracks/{mmsi}/{from_date}/{to_date}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    return response.json()


def get_historic_positions_from_mmsi(mmsi: int):
    for ais in get_historic_ais(mmsi)[0::40]:
        yield ais["latitude"], ais["longitude"]


if __name__ == "__main__":
    print(*get_historic_positions_from_mmsi(219025221))
