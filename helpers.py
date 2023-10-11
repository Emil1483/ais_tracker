from math import pi, cos, asin, sqrt


def distance(pos1, pos2):
    lat1, lon1 = pos1
    lat2, lon2 = pos2

    r = 6371
    p = pi / 180

    a = (
        0.5
        - cos((lat2 - lat1) * p) / 2
        + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
    )
    return 2 * r * asin(sqrt(a))
