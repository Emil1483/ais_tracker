import requests
import os
from dotenv import load_dotenv


def get_access_token():
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

    print(results)

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


if __name__ == "__main__":
    print(get_position_from_mmsi(257728000))
    print(search_for_vessel("OCEANIC VEGA"))