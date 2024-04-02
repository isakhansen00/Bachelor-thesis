from pyModeS import common

def airborne_position_with_ref(msg, lat_ref, lon_ref):
    """Decode airborne position with only one message,
    knowing reference nearby location, such as previously calculated location,
    ground station, or airport location, etc. The reference position shall
    be with in 180NM of the true position.

    Args:
        msg (str): even message (28 hexdigits)
        lat_ref: previous known latitude
        lon_ref: previous known longitude

    Returns:
        (float, float): (latitude, longitude) of the aircraft
    """

    mb = common.hex2bin(msg)[32:]

    cprlat = common.bin2int(mb[22:39]) / 131072.0
    cprlon = common.bin2int(mb[39:56]) / 131072.0

    i = int(mb[21])
    d_lat = 360.0 / 59 if i else 360.0 / 60

    j = common.floor(lat_ref / d_lat) + common.floor(
        0.5 + ((lat_ref % d_lat) / d_lat) - cprlat
    )

    lat = d_lat * (j + cprlat)

    ni = common.cprNL(lat) - i

    if ni > 0:
        d_lon = 360.0 / ni
    else:
        d_lon = 360.0

    m = common.floor(lon_ref / d_lon) + common.floor(
        0.5 + ((lon_ref % d_lon) / d_lon) - cprlon
    )

    lon = d_lon * (m + cprlon)

    return round(lat, 5), round(lon, 5)


