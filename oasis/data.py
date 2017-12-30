from time import strptime
from oasis.datasources import BusinessLicenses, CensusTracts, Neighborhoods, NeighborhoodTractsMap, Socioeconomic

business_licenses_db = BusinessLicenses()
census_tracts_db = CensusTracts()
neighborhoods_db = Neighborhoods()
neighborhood_tracts_map_db = NeighborhoodTractsMap()
socioeconomic_db = Socioeconomic()

# Cache of previously computed requests; improves performance several order of magnitude
_cached_license_date_start = {}
_cached_license_date_end = {}
_cached_license_codes = None
_cached_license_desc = {}
_cached_licenses = {}
_cached_centroids = {}
_cached_tracts_in_neighborhood = {}
_cached_neighborhood_ids = []
_cached_neighborhood_names = {}
_cached_tract_ids = []


def get_census_tract_ids():
    """
    Returns a set containing the census tract ID of every census tract in Chicago.
    :return: A set of census tract IDs. For example, (020301, 020302, ...)
    """
    global _cached_tract_ids
    if len(_cached_tract_ids) > 0:
        return _cached_tract_ids

    tracts = census_tracts_db.as_dictionary()
    ids = set()
    for tract in tracts:
        ids.add(tract[census_tracts_db.ROW_GEOID])

    _cached_tract_ids = ids
    return ids


def get_neighborhood_ids():
    """
    Returns a set of Chicago community area ids (a number between 1 and 77 identifying the neighborhood). Provided the
    city does not annex or de-annex neighborhoods, this should always result in a set equal to range(1,78).
    :return: A set of community IDs. For example, (1, 2, 3, ... 77)
    """
    global _cached_neighborhood_ids
    if len(_cached_neighborhood_ids) > 0:
        return _cached_neighborhood_ids

    neighborhoods = neighborhoods_db.as_dictionary()
    ids = set()
    for neighborhood in neighborhoods:
        ids.add(neighborhood[neighborhoods_db.ROW_AREA_NUMBER])

    _cached_neighborhood_ids = ids
    return ids


def get_neighborhood_name(neighborhood_id):
    """
    Gets the name of the neighborhood referenced by ID.
    :param neighborhood_id: A community area ID (as returned by get_neighborhood_ids)
    :return: The name of the neighborhood in all uppercase. For example, "LINCOLN PARK"
    """
    global _cached_neighborhood_names
    if neighborhood_id in _cached_neighborhood_names:
        return _cached_neighborhood_names[neighborhood_id]

    neighborhoods = neighborhoods_db.as_dictionary()
    for neighborhood in neighborhoods:
        if neighborhood[neighborhoods_db.ROW_AREA_NUMBER] == neighborhood_id:
            _cached_neighborhood_names[neighborhood_id] = neighborhood[neighborhoods_db.ROW_AREA_NAME].upper()
            return _cached_neighborhood_names[neighborhood_id]


def get_census_tracts_in_neighborhood(neighborhood_id):
    """
    Gets a set of census tract IDs that make up a given neighborhood.
    :param neighborhood_id: The ID of the neighborhood to be returned
    :return:
    """

    global _cached_tracts_in_neighborhood
    if neighborhood_id in _cached_tracts_in_neighborhood:
        return _cached_tracts_in_neighborhood[neighborhood_id]

    mapping_data = neighborhood_tracts_map_db.as_dictionary()
    tracts = list()
    for mapping in mapping_data:
        if neighborhood_id == mapping[neighborhood_tracts_map_db.ROW_AREA_NUMBER]:
            tracts.append(mapping[neighborhood_tracts_map_db.ROW_TRACT_GEOID])

    _cached_tracts_in_neighborhood[neighborhood_id] = tracts
    return tracts


def get_census_centroid(census_tract_id):
    """
    Gets a pair of decimal coordinates representing the geographic center (centroid) of the requested census tract.
    :param census_tract_id:
    :return:
    """
    global _cached_centroids
    if census_tract_id in _cached_centroids:
        return _cached_centroids[census_tract_id]

    tracts = census_tracts_db.as_dictionary()
    for tract in tracts:
        if geoid_matches(census_tract_id, tract[census_tracts_db.ROW_GEOID]):
            _cached_centroids[census_tract_id] = float(tract[census_tracts_db.ROW_LATITUDE]), float(tract[census_tracts_db.ROW_LONGITUDE])
            return _cached_centroids[census_tract_id]


def geoid_matches(geo1, geo2):
    return geo1 in geo2 or geo2 in geo1


def get_license_date_range(license_code):
    _initialize_license_cache()
    global _cached_license_date_start, _cached_license_date_end
    return _cached_license_date_start[license_code], _cached_license_date_end[license_code]


def get_licenses(license_code):
    _initialize_license_cache()
    global _cached_licenses
    return sorted(_cached_licenses[license_code])


def get_license_years(row):
    start_string = row[business_licenses_db.ROW_LICENSE_TERM_START_DATE]
    end_string = row[business_licenses_db.ROW_LICENSE_TERM_END_DATE]

    if start_string and end_string:
        start_year = strptime(start_string, "%m/%d/%Y").tm_year
        end_year = strptime(end_string, "%m/%d/%Y").tm_year
    else:
        return None, None

    return start_year, end_year


def get_license_codes():
    """
    Gets a set of unique license codes identifying each type of license issued by Chicago.
    :return: A set of unique license codes.
    """
    _initialize_license_cache()
    global _cached_license_codes
    return _cached_license_codes


def get_license_description(license_code):
    _initialize_license_cache()

    global _cached_license_desc
    return _cached_license_desc[license_code]


def encode_license_description(license_desc):
    return license_desc.lower()\
        .replace(" ", "-")\
        .replace(",", "")\
        .replace("(", "")\
        .replace(")", "")\
        .replace("'", "")


def download_all():
    global business_licenses_db, census_tracts_db, neighborhoods_db, neighborhood_tracts_map_db
    business_licenses_db = BusinessLicenses(True)
    census_tracts_db = CensusTracts(True)
    neighborhoods_db = Neighborhoods(True)
    Socioeconomic(True)
    neighborhood_tracts_map_db = NeighborhoodTractsMap()


def _initialize_license_cache():
    global _cached_license_date_start,_cached_license_date_end ,_cached_license_codes,_cached_license_desc,_cached_licenses

    # Cache is initialized
    if _cached_licenses:
        return

    print("Rebuilding license cache...")

    _cached_license_date_start = {}
    _cached_license_date_end = {}
    _cached_license_codes = set()
    _cached_license_desc = {}
    _cached_licenses = {}

    for license in business_licenses_db.as_dictionary():
        license_code = license[business_licenses_db.ROW_LICENSE_CODE]
        license_desc = license[business_licenses_db.ROW_LICENSE_DESCRIPTION]
        license_start = license[business_licenses_db.ROW_LICENSE_TERM_START_DATE]
        license_end = license[business_licenses_db.ROW_LICENSE_TERM_END_DATE]

        if license_start and license_end:
            start_year = strptime(license_start, "%m/%d/%Y").tm_year
            end_year = strptime(license_end, "%m/%d/%Y").tm_year

        if license_code not in _cached_license_date_start:
            _cached_license_date_start[license_code] = start_year
        if start_year < _cached_license_date_start[license_code]:
            _cached_license_date_start[license_code] = start_year

        if license_code not in _cached_license_date_end:
            _cached_license_date_end[license_code] = end_year
        if end_year > _cached_license_date_end[license_code]:
            _cached_license_date_end[license_code] = end_year

        if license_desc and license_code:
            _cached_license_desc[license_code] = license_desc

        if license_code:
            if license_code not in _cached_licenses:
                _cached_licenses[license_code] = list()
            _cached_licenses[license_code].append(license)

        _cached_license_codes.add(license_code)



    print(" ... done.")
