import math


def distance_lat_lng(lat1, lon1, lat2, lon2, units='m'):
    """
    Calculates the distance between two coordinates represented in decimal radians in the specified units of measure.

    For example, assume Chicago is (41.881832, -87.623177) and New York City is (40.712772, -74.006058); invoking this
    function as distance_lat_lng(41.881832, -87.623177, 40.712772, -74.006058, 'm') will return ~710.6 (miles).

    Based on an algorithm published by GeoDataSource, http://www.geodatasource.com

    :param lat1: First coordinate latitude, in decimal degrees
    :param lon1: First coordinate longitude, in decimal degrees
    :param lat2: Second coordinate latitude, in decimal degrees
    :param lon2: Second coordinate longitude, in decimal degrees
    :param units: Units of measure; 'm' for statute miles, 'k' for kilometers or 'n' for nautical miles
    :return: Distance between (lat1, lon1) and (lat2, long2) in the given units of measure.
    """

    lat1rad = math.radians(float(lat1))
    lon1rad = math.radians(float(lon1))
    lat2rad = math.radians(float(lat2))
    lon2rad = math.radians(float(lon2))

    return distance_lat_lng_rad(lat1rad, lon1rad, lat2rad, lon2rad, units)


def distance_lat_lng_rad(lat1rad, lon1rad, lat2rad, lon2rad, units):
    """
    Calculates the distance between two coordinates represented in decimal radians in the specified units of measure.

    :param lat1rad: First coordinate latitude, in decimal radians
    :param lon1rad: First coordinate longitude, in decimal radians
    :param lat2rad: Second coordinate latitude, in decimal radians
    :param lon2rad: Second coordinate longitude, in decimal radians
    :param units: Units of measure; 'm' for statute miles, 'k' for kilometers or 'n' for nautical miles
    :return: The distance between (lat1rad, lon1rad) and (lat2rad, lon2rad) in the given unit of measure
    """
    theta = lon1rad - lon2rad
    dist = math.sin(lat1rad) * math.sin(lat2rad) + math.cos(lat1rad) * math.cos(lat2rad) * math.cos(theta)
    dist = math.acos(dist)
    dist = math.degrees(dist)
    dist = dist * 60.0 * 1.1515

    if units == 'k':
        dist = dist * 1.609344
    elif units == 'n':
        dist = dist * 0.8684

    return dist
