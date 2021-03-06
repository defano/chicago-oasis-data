from time import strptime
from oasis.datasources import BusinessLicenses, CensusTracts, Neighborhoods, NeighborhoodTractsMap, Socioeconomic

# Cache of data sources
license_db = BusinessLicenses()
census_tracts_db = CensusTracts()
neighborhood_db = Neighborhoods()
neighborhood_tracts_map_db = NeighborhoodTractsMap()
socioeconomic_db = Socioeconomic()

# Cache of previously computed requests; improves performance several order of magnitude
_cached_neighborhood_ids = []           # Cached set of neighborhood ids (community area numbers, 1..77)
_cached_tract_ids = set()               # Cached set of census tract ids
_cached_neighborhood_names = {}         # Map of neighborhood id (1..77) to neighborhood name
_cached_tracts_in_neighborhood = {}     # Map of neighborhood id (1..77) to list of census tract ids
_cached_tract_pops = {}                 # Map of census_tract_id to population
_cached_centroids = {}                  # Map of census_tract_id to centroid (lat, lng)
_cached_license_date_start = {}         # Map of license code to first year with license records
_cached_license_date_end = {}           # Map of license_code to last year with license records
_cached_license_codes = set()           # Cached set of unique license codes
_cached_license_desc = {}               # Map of license_code to license_description
_cached_licenses = {}                   # Map of license_code to license_record[]
_cached_business_years = {}             # Map of license_number to (license_start_year, license_end_year)
_cached_business_dba = {}               # Map of license_number to doing-business-as name
_cached_business_legal = {}             # Map of license_number to legal name
_cached_business_loc = {}               # Map of license_number to (lat, lng)
_cached_business_addr = {}              # Map of license_number to address
_cached_business_city = {}              # Map of license_number to city
_cached_business_state = {}             # Map of license_number to state
_cached_business_zip = {}               # Map of license_number to zip


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

    neighborhoods = neighborhood_db.as_dictionary()
    ids = set()
    for neighborhood in neighborhoods:
        ids.add(neighborhood[neighborhood_db.ROW_AREA_NUMBER])

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

    neighborhoods = neighborhood_db.as_dictionary()
    for neighborhood in neighborhoods:
        if neighborhood[neighborhood_db.ROW_AREA_NUMBER] == neighborhood_id:
            _cached_neighborhood_names[neighborhood_id] = neighborhood[neighborhood_db.ROW_AREA_NAME].upper()
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


def get_census_population(census_tract_id):
    """
    Returns the population of the requested census tract.
    :param census_tract_id: The census tract id
    :return: The population of the census tract
    """
    global _cached_tract_pops
    if census_tract_id in _cached_tract_pops:
        return _cached_tract_pops[census_tract_id]

    for tract in census_tracts_db.as_dictionary():
        _cached_tract_pops[convert_geo_id_to_tract_id(tract[census_tracts_db.ROW_GEOID])] = tract[census_tracts_db.ROW_POPULATION]
    return _cached_tract_pops[census_tract_id]


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
        if tract_id_equals(census_tract_id, tract[census_tracts_db.ROW_GEOID]):
            _cached_centroids[census_tract_id] = float(tract[census_tracts_db.ROW_LATITUDE]), float(tract[census_tracts_db.ROW_LONGITUDE])
            return _cached_centroids[census_tract_id]


def convert_geo_id_to_tract_id(geo_id):
    """
    Converts an 11-digit GEOID to a Chicago census tract id. (Assumes the geo_id refers to a place in Chicago).
    :param geo_id: The US Census Gazetteer GEOID to convert.
    :return: The last six digits of the GEOID, equivalent to the census tract id.
    """
    return geo_id[-6:]


def tract_id_equals(tract_id, geo_id):
    """
    Determines if a 11-digit GEOID (from the US census files) refers to the same place as a six-digit Chicago census
    tract ID.

    :param tract_id: A 6-digit Chicago census tract ID (i.e., '821402')
    :param geo_id: An 11-digit GEOID from the US Census "Gazetteer" files (i.e., '17031821402')
    :return: True if equivalent, False otherwise
    """
    return geo_id.startswith("1703") and tract_id == geo_id[-6:]


def get_license_date_range(license_code):
    """
    Gets a pair of years indicating the earliest latest date for which data is available for the given license code.
    :param license_code: The license code
    :return: A pair of (earliest_date, latest_date)
    """
    global _cached_license_date_start, _cached_license_date_end
    return _cached_license_date_start[license_code], _cached_license_date_end[license_code]


def get_licenses(license_code):
    """
    Returns a list of business license records associated with the given license code. Each record is a map of row name
    to row value. Only "required" rows are returned in the result set. See the datasources module for information about
    required rows.
    :param license_code: The license code of the licenses to return
    :return: A list of business license record dictionaries.
    """
    global _cached_licenses
    return _cached_licenses[license_code]


def get_business_years(license_number):
    """
    Retuns a set of four-digit years containing every year for which data exists.
    :param license_number: The license number whose license year range should be returned.
    :return: A set of years in which the business was active.
    """
    global _cached_business_years
    return _cached_business_years[license_number]


def get_license_codes():
    """
    Gets a set of unique license codes identifying each type of license issued by Chicago.
    :return: A set of unique license codes.
    """
    global _cached_license_codes
    return sorted(_cached_license_codes)


def get_license_description(license_code):
    """
    Gets the description of the given license code. For example, license code '1002' results in 'Accessory Garage'
    :param license_code: The license code
    :return: The license description
    """
    global _cached_license_desc
    return _cached_license_desc[license_code]


def get_business_dba(license_number):
    """
    Gets the name under which the business is "doing business as". Returns "UNDEFINED" if no DBA is registered.
    :param license_number: The business' license number
    :return: The business' DBA name
    """
    global _cached_business_dba

    if license_number in _cached_business_dba:
        return _cached_business_dba[license_number]
    else:
        return "UNDEFINED"


def get_business_legal_name(license_number):
    """
    Gets the legal name of the business. Returns "UNDEFINED" if no legal name is registered.
    :param license_number: The business' license number
    :return: The business' legal name
    """
    global _cached_business_legal

    if license_number in _cached_business_legal:
        return _cached_business_legal[license_number]
    else:
        return "UNDEFINED"


def get_business_lat_lng(license_number):
    """
    Gets a pair indicating the latitude and longitude of the business address; returns (0.0, 0.0) no lat/lng is
    available.
    :param license_number: The business' license number
    :return: The lat/lng of the business
    """
    global _cached_business_loc

    if license_number in _cached_business_loc:
        return _cached_business_loc[license_number]
    else:
        return 0.0, 0.0


def get_business_address(license_number):
    """
    Gets the street address of the business; returns "UNDEFINED" in no address is available.
    :param license_number: The business' license number
    :return: The street address of the business, for example "222 SOUTH RIVERSIDE PLZ"
    """
    global _cached_business_addr

    if license_number in _cached_business_addr:
        return _cached_business_addr[license_number]
    else:
        return "UNDEFINED"


def get_business_city(license_number):
    """
    Gets the city associated with the business' address; should always be "CHICAGO". Returns "UNDEFINED" if no city
    is available.
    :param license_number: The business' license number.
    :return: The name of the city listed in the business' address
    """
    global _cached_business_city

    if license_number in _cached_business_city:
        return _cached_business_city[license_number]
    else:
        return "UNDEFINED"


def get_business_state(license_number):
    """
    Gets the state zip abbreviation associated with the business' address; should always be "IL". Returns "UNDEFINED"
    if no state is available.
    :param license_number: The business' license number
    :return: The two-letter state abbreviation associated with the business address
    """
    global _cached_business_state

    if license_number in _cached_business_state:
        return _cached_business_state[license_number]
    else:
        return "UNDEFINED"


def get_business_zip(license_number):
    """
    Gets the zip code associated with the business' address; returns "UNDEFINED" if no zip code is available.
    :param license_number: The business' license number.
    :return: The business' zip code
    """
    global _cached_business_zip

    if license_number in _cached_business_zip:
        return _cached_business_zip[license_number]
    else:
        return "UNDEFINED"


def get_license_file_key(license_desc):
    """
    Converts a license description to a file and URL-safe string. For example, "Music and Dance" becomes
    "music-and-dance".
    :param license_desc: The license description to encode
    :return: The encoded license description
    """
    return license_desc.lower()\
        .replace(" - ", "-")\
        .replace(" ", "-")\
        .replace(",", "")\
        .replace("(", "")\
        .replace(")", "")\
        .replace("'", "")\
        .replace("/", "-")\
        .replace("\\", "-")\
        .replace(";", "")


def download_all():
    """
    Mark all datasets as needing download.
    :return: None
    """
    global license_db, census_tracts_db, neighborhood_db, neighborhood_tracts_map_db
    license_db = BusinessLicenses(True)
    census_tracts_db = CensusTracts(True)
    neighborhood_db = Neighborhoods(True)
    Socioeconomic(True)
    neighborhood_tracts_map_db = NeighborhoodTractsMap()


def initialize_license_cache():
    """
    Builds a set of caches used by this module to provide fast data lookups. This method _must_ be called before any
    other methods in this module are used
    :return: None
    """
    global _cached_license_date_start, _cached_license_date_end, _cached_license_codes
    global _cached_license_desc, _cached_licenses, _cached_business_dba, _cached_business_legal, _cached_business_loc
    global _cached_business_addr, _cached_business_city, _cached_business_state, _cached_business_zip
    global _cached_business_years

    # Cache is already initialized
    if _cached_licenses:
        return

    print("Building license data caches...")

    _cached_license_date_start = {}     # Map of license code to first year with license records
    _cached_license_date_end = {}       # Map of license_code to last year with license records
    _cached_license_codes = set()       # Cached set of unique license codes
    _cached_license_desc = {}           # Map of license_code to license_description
    _cached_licenses = {}               # Map of license_code to license_record[]
    _cached_business_years = {}         # Map of license_number to (license_start_year, license_end_year)
    _cached_business_dba = {}           # Map of license_number to doing-business-as name
    _cached_business_legal = {}         # Map of license_number to legal name
    _cached_business_loc = {}           # Map of license_number to (lat, lng)
    _cached_business_addr = {}          # Map of license_number to address
    _cached_business_city = {}          # Map of license_number to city
    _cached_business_state = {}         # Map of license_number to state
    _cached_business_zip = {}           # Map of license_number to zip

    dup_licenses = set()

    for license in license_db.as_dictionary():
        license_code = license[license_db.ROW_LICENSE_CODE]
        license_desc = license[license_db.ROW_LICENSE_DESCRIPTION]
        license_start = license[license_db.ROW_LICENSE_TERM_START_DATE]
        license_end = license[license_db.ROW_LICENSE_TERM_END_DATE]
        license_number = license[license_db.ROW_LICENSE_NUMBER]
        business_dba = license[license_db.ROW_BUSINESS_DBA]
        business_legal = license[license_db.ROW_BUSINESS_LEGAL_NAME]
        business_address = license[license_db.ROW_BUSINESS_ADDRESS]
        business_state = license[license_db.ROW_BUSINESS_STATE]
        business_zip = license[license_db.ROW_BUSINESS_ZIP]
        business_city = license[license_db.ROW_BUSINESS_CITY]
        business_lat = license[license_db.ROW_LATITUDE]
        business_lng = license[license_db.ROW_LONGITUDE]

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
            _cached_license_codes.add(license_code)

            if license_code not in _cached_licenses:
                _cached_licenses[license_code] = list()

            if license_number not in dup_licenses:
                _cached_licenses[license_code].append(license_db.required_rows_copy(license))
                _cached_business_years[license_number] = (start_year, end_year)
                dup_licenses.add(license_number)
            else:
                if start_year < _cached_business_years[license_number][0]:
                    _cached_business_years[license_number] = (start_year, _cached_business_years[license_number][1])
                if end_year > _cached_business_years[license_number][1]:
                    _cached_business_years[license_number] = (_cached_business_years[license_number][0], end_year)

        if business_dba and license_number not in _cached_business_dba:
            _cached_business_dba[license_number] = business_dba

        if business_legal and license_number not in _cached_business_legal:
            _cached_business_legal[license_number] = business_legal

        if business_lng and business_lat and license_number not in _cached_business_loc:
            _cached_business_loc[license_number] = (business_lat, business_lng)

        if business_address and license_number not in _cached_business_addr:
            _cached_business_addr[license_number] = business_address

        if business_city and license_number not in _cached_business_city:
            _cached_business_city[license_number] = business_city

        if business_state and license_number not in _cached_business_state:
            _cached_business_state[license_number] = business_state

        if business_zip and license_number not in _cached_business_zip:
            _cached_business_zip[license_number] = business_zip
