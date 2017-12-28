import urllib2
import tempfile
import os.path
import csv
import fileinput

CHICAGO_BUSINESS_LICENSES_REMOTE = "http://data.cityofchicago.org/api/views/r5kz-chrr/rows.csv?accessType=DOWNLOAD&api_foundry=true"
CHICAGO_BUSINESS_LICENSES_LOCAL = "chicago_business_licenses.csv"

CHICAGO_GROCERY_STORES_REMOTE = "http://data.cityofchicago.org/api/views/53t8-wyrc/rows.csv?accessType=DOWNLOAD&api_foundry=true"
CHICAGO_GROCERY_STORES_LOCAL = "chicago_grocery_stores.csv"

CENSUS_TRACT_TO_NEIGHBORHOOD_LOCAL = "../data/census_tract_to_neighborhood.csv"

CHICAGO_NEIGHBORHOOD_AREAS_REMOTE = "http://data.cityofchicago.org/api/views/igwz-8jzy/rows.csv?accessType=DOWNLOAD&api_foundry=true"
CHICAGO_NEIGHBORHOOD_AREAS_LOCAL = "chicago_neighborhoods.csv"

CHICAGO_SOCIOECONOMIC_REMOTE = "https://data.cityofchicago.org/resource/jcxq-k9xf.csv"
CHICAGO_SOCIOECONOMIC_LOCAL = "chicago_socioeconomic.csv"

CHICAGO_HEALTH_REMOTE = "https://data.cityofchicago.org/resource/gtem-tu7s.csv"
CHICAGO_HEALTH_LOCAL = "chicago_health.csv"

ILL_CENSUS_TRACTS_REMOTE = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/census_tracts_list_17.txt"
ILL_CENSUS_TRACTS_LOCAL = "illinois_census_tracts.tsv"


def get_business_licenses_database():
    return csv.DictReader(open(__business_licenses_path(), 'rb'))


def get_neighborhoods_database():
    return csv.DictReader(open(__neighborhoods_path(), 'rb'))


def get_census_tracts_database():
    # This bit of stupidity required to strip trailing whitespace from last column (and column header)
    for line in fileinput.input(__illinois_census_tracts_path(), inplace=True):
        print "%s" % line.strip()

    csv.register_dialect('CensusTSV', delimiter='\t', skipinitialspace=True, quoting=csv.QUOTE_NONE)
    return csv.DictReader(open(__illinois_census_tracts_path(), 'rb'), dialect="CensusTSV")


def get_census_neighborhood_map_database():
    return csv.DictReader(open(__census_to_neighborhood_mapping_path(), 'rb'))


def __business_licenses_path(force_reload=False):
    """
    Returns the filesystem path of the business license data file, downloading it first if needed.

    :param force_reload: When True, causes the file to be downloaded even if a cached copy exists.
    :return: An absolute filesystem path to the file containing the fetched data.
    """
    return __read_cache(CHICAGO_BUSINESS_LICENSES_REMOTE, CHICAGO_BUSINESS_LICENSES_LOCAL, force_reload)


def __grocery_stores_path(force_reload=False):
    """
    Returns the filesystem path of the grocery store data file, downloading it first if needed.

    :param force_reload: When True, causes the file to be downloaded even if a cached copy exists.
    :return: An absolute filesystem path to the file containing the fetched data.
    """
    return __read_cache(CHICAGO_GROCERY_STORES_REMOTE, CHICAGO_BUSINESS_LICENSES_LOCAL, force_reload)


def __census_to_neighborhood_mapping_path():
    """
    Returns the filesystem path of the census tract to neighborhood mapping file (data file is local to the project).

    :return: An absolute filesystem path to the file containing the fetched data.
    """
    my_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(my_path, CENSUS_TRACT_TO_NEIGHBORHOOD_LOCAL)


def __illinois_census_tracts_path(force_reload=False):
    """
    Returns the filesystem path of the Illinois census tract data file, downloading it first if needed.

    :param force_reload: When True, causes the file to be downloaded even if a cached copy exists.
    :return: An absolute filesystem path to the file containing the fetched data.
    """
    return __read_cache(ILL_CENSUS_TRACTS_REMOTE, ILL_CENSUS_TRACTS_LOCAL, force_reload)


def __neighborhoods_path(force_reload=False):
    """
    Returns the filesystem path of the Chicago neighborhoods data file, downloading it first if needed.

    :param force_reload: When True, causes the file to be downloaded even if a cached copy exists.
    :return: An absolute filesystem path to the file containing the fetched data.
    """
    return __read_cache(CHICAGO_NEIGHBORHOOD_AREAS_REMOTE, CHICAGO_NEIGHBORHOOD_AREAS_LOCAL, force_reload)


def __socioeconomic_path(force_reload=False):
    """
    Returns the filesystem path of the Chicago socioeconomic data file, downloading it first if needed.

    :param force_reload: When True, causes the file to be downloaded even if a cached copy exists.
    :return: An absolute filesystem path to the file containing the fetched data.
    """
    return __read_cache(CHICAGO_SOCIOECONOMIC_REMOTE, CHICAGO_SOCIOECONOMIC_LOCAL, force_reload)


def __health_path(force_reload=False):
    """
    Returns the filesystem path of the Chicago health statistics data file, downloading it first if needed.

    :param force_reload: When True, causes the file to be downloaded even if a cached copy exists.
    :return: An absolute filesystem path to the file containing the fetched data.
    """
    return __read_cache(CHICAGO_HEALTH_REMOTE, CHICAGO_HEALTH_LOCAL, force_reload)


def __get_cache_file_path(filename):
    """
    Appends the given value to the system's temp directory.
    :param filename: The name of the file
    :return:
    """
    return tempfile.gettempdir() + '/' + filename


def __read_cache(url, dataset_name, force_reload=False):
    """
    Returns the requested dataset, downloading it and storing it in the cache if needed.

    :param url: The URL where the dataset can be downloaded from (if need be)
    :param dataset_name: The name of the dataset (the cache key)
    :param force_reload: When true, data will be downloaded from server even if it's in the cache
    :return: An absolute path to the data saved on the local filesystem
    """
    cache_file_path = __get_cache_file_path(dataset_name)
    if os.path.exists(cache_file_path) and not force_reload:
        print("Getting cached data from " + cache_file_path)
        return cache_file_path
    else:
        print("Downloading data from " + url + ". (It's going to space, give it a minute.)")
        return __load_cache(url, cache_file_path)


def __load_cache(url, cache_file_path):
    """
    Downloads the given URL and stores the data at the given file path.
    :param url: The URL to be loaded
    :param cache_file_path: The location on the filesystem where the data should be written
    :return: cache_file_path
    """
    cache_file = open(cache_file_path, 'w')
    data = urllib2.urlopen(url)
    try:
        cache_file.write(data.read())
        print(cache_file)
    finally:
        cache_file.close()
    return cache_file_path


def __download_data():
    """
    Forcibly reloads all data from the server; for test purposes only.
    :return: None
    """
    __neighborhoods_path(True)
    __grocery_stores_path(True)
    __business_licenses_path(True)
    __illinois_census_tracts_path(True)
    __health_path(True)
    __socioeconomic_path(True)

get_business_licenses_database()