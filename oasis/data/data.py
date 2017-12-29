from oasis.data.BusinessLicenses import BusinessLicenses
from oasis.data.CensusTracts import CensusTracts
from oasis.data.Neighborhoods import Neighborhoods
from oasis.data.NeighborhoodTractsMap import NeighborhoodTractsMap
from time import strptime

business_licenses_db = BusinessLicenses()
census_tracts_db = CensusTracts()
neighborhoods_db = Neighborhoods()
neighborhood_tracts_map_db = NeighborhoodTractsMap()

_cached_license_date_range = {}
_cached_license_types = None
_cached_licenses = {}
_cached_centroids = {}
_cached_tracts_in_neighborhood = {}
_cached_neighborhood_ids = []
_cached_tract_ids = []


def get_census_tract_ids():
    global _cached_tract_ids
    if len(_cached_tract_ids) > 0:
        return _cached_tract_ids

    tracts = census_tracts_db.get_dictionary()
    ids = set()
    for tract in tracts:
        ids.add(tract[census_tracts_db.ROW_GEOID])

    _cached_tract_ids = ids
    return ids


def get_neighborhood_ids():
    global _cached_neighborhood_ids
    if len(_cached_neighborhood_ids) > 0:
        return _cached_neighborhood_ids

    neighborhoods = neighborhoods_db.get_dictionary()
    ids = set()
    for neighborhood in neighborhoods:
        ids.add(neighborhood[neighborhoods_db.ROW_AREA_NUMBER])

    _cached_neighborhood_ids = ids
    return ids


def get_census_tracts_in_neighborhood(area_number):
    global _cached_tracts_in_neighborhood
    if area_number in _cached_tracts_in_neighborhood:
        return _cached_tracts_in_neighborhood[area_number]

    mapping_data = neighborhood_tracts_map_db.get_dictionary()
    tracts = list()
    for mapping in mapping_data:
        if area_number == mapping[neighborhood_tracts_map_db.ROW_AREA_NUMBER]:
            tracts.append(mapping[neighborhood_tracts_map_db.ROW_TRACT_GEOID])

    _cached_tracts_in_neighborhood[area_number] = tracts
    return tracts


def get_census_centroid(geoid):
    global _cached_centroids
    if geoid in _cached_centroids:
        return _cached_centroids[geoid]

    tracts = census_tracts_db.get_dictionary()
    for tract in tracts:
        if geoid_matches(geoid, tract[census_tracts_db.ROW_GEOID]):
            _cached_centroids[geoid] = float(tract[census_tracts_db.ROW_LATITUDE]), float(tract[census_tracts_db.ROW_LONGITUDE])
            return _cached_centroids[geoid]


def geoid_matches(geo1, geo2):
    return geo1 in geo2 or geo2 in geo1


def get_license_date_range(license_code):
    global _cached_license_date_range
    if license_code in _cached_license_date_range:
        return _cached_license_date_range[license_code]

    earliest, latest = None, None

    for row in get_licenses(license_code):
        start_string = row[business_licenses_db.ROW_LICENSE_TERM_START_DATE]
        end_string = row[business_licenses_db.ROW_LICENSE_TERM_END_DATE]

        if start_string and end_string:
            start = strptime(row[business_licenses_db.ROW_LICENSE_TERM_START_DATE], "%m/%d/%Y")
            end = strptime(row[business_licenses_db.ROW_LICENSE_TERM_END_DATE], "%m/%d/%Y")

            if earliest is None or start < earliest:
                earliest = start

            if latest is None or end > latest:
                latest = end

    _cached_license_date_range[license_code] = (earliest, latest)
    return earliest, latest


def get_licenses(license_code):
    global _cached_licenses
    if license_code in _cached_licenses:
        return _cached_licenses[license_code]

    business_data = business_licenses_db.get_dictionary()
    licenses = list()
    for row in business_data:
        if row[business_licenses_db.ROW_LICENSE_CODE] == license_code:
            licenses.append(row)

    _cached_licenses[license_code] = licenses
    return licenses


def filter_by_year(license_data, year):
    year = str(year)
    licenses = list()
    for row in license_data:
        start_year, end_year = get_license_years(row)
        if start_year <= int(year) <= end_year:
            licenses.append(row)
    return licenses


def get_license_years(row):
    start_string = row[business_licenses_db.ROW_LICENSE_TERM_START_DATE]
    end_string = row[business_licenses_db.ROW_LICENSE_TERM_END_DATE]

    if start_string and end_string:
        start_year = strptime(start_string, "%m/%d/%Y").tm_year
        end_year = strptime(end_string, "%m/%d/%Y").tm_year
    else:
        return None, None

    return start_year, end_year


def get_license_types():
    """
    Gets information about each type of license issues by the City of Chicago.
    :return: A tuple containing the license code, license description and associated business activity.
    """
    global _cached_license_types
    if _cached_license_types is not None:
        return _cached_license_types

    business_data = business_licenses_db.get_dictionary()
    licenses = set()
    for row in business_data:
        licenses.add((
            row[business_licenses_db.ROW_LICENSE_CODE].lower(),
            row[business_licenses_db.ROW_LICENSE_DESCRIPTION],
            row[business_licenses_db.ROW_BUSINESS_ACTIVITY]))

    _cached_license_types = licenses
    return licenses
