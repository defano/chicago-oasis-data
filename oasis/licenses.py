import oasis.data
import time


_cached_license_date_range = {}
_cached_license_types = None
_cached_licenses = {}


def get_license_date_range(license_code):
    global _cached_license_date_range
    if license_code in _cached_license_date_range:
        return _cached_license_date_range[license_code]

    print("Getting license date range for license code " + license_code)
    earliest, latest = None, None

    for row in get_licenses(license_code):
        start_string = row['LICENSE TERM START DATE']
        end_string = row['LICENSE TERM EXPIRATION DATE']

        if start_string and end_string:
            start = time.strptime(row['LICENSE TERM START DATE'], "%m/%d/%Y")
            end = time.strptime(row['LICENSE TERM EXPIRATION DATE'], "%m/%d/%Y")

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

    print("Getting licenses of code " + license_code)
    business_data = oasis.data.get_business_licenses_database()
    licenses = list()
    for row in business_data:
        if row['LICENSE CODE'] == license_code:
            licenses.append(row)

    _cached_licenses[license_code] = licenses
    return licenses


def filter_by_year(license_data, year):
    year = str(year)
    print("Getting business licenses active in year " + year)
    ref_year = time.strptime(year, "%Y")
    licenses = list()
    for row in license_data:
        start_string = row['LICENSE TERM START DATE']
        end_string = row['LICENSE TERM EXPIRATION DATE']

        if start_string and end_string:
            start_year = time.strptime(row['LICENSE TERM START DATE'], "%m/%d/%Y").tm_year
            end_year = time.strptime(row['LICENSE TERM EXPIRATION DATE'], "%m/%d/%Y").tm_year
            if start_year <= int(year) <= end_year:
                licenses.append(row)

    return licenses


def get_license_types():
    """
    Gets information about each type of license issues by the City of Chicago.
    :return: A tuple containing the license code, license description and associated business activity.
    """
    global _cached_license_types
    if _cached_license_types is not None:
        return _cached_license_types

    print("Determining unique license types")
    business_data = oasis.data.get_business_licenses_database()
    licenses = set()
    for row in business_data:
        if 'LICENSE CODE' in row and 'LICENSE DESCRIPTION' in row and 'BUSINESS ACTIVITY' in row:
            licenses.add((row['LICENSE CODE'].lower(), row['LICENSE DESCRIPTION'], row['BUSINESS ACTIVITY']))

    _cached_license_types = licenses
    return licenses
