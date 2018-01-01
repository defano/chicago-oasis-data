import csv
import os.path
import tempfile
import urllib2


class DataSet:

    def __init__(self, force_reload=False):
        self.__force_reload = force_reload

    def as_dictionary(self):
        return self.validate(csv.DictReader(open(self.read_cache(), 'rb')))

    def get_remote_url(self):
        raise Exception("Bug! Not implemented in subclass.")

    def get_local_filename(self):
        raise Exception("Bug! Not implemented in subclass.")

    def preprocess(self, data):
        """
        Performs any required transformation on the downloaded data prior to it being used in analysis.

        Override in subclasses to allow different data sources to be pre-processed differently. Datasets that require
        no pre-processing should simply return the input argument.

        :param data: The data to be pre-processed
        :return: The pre-processed data; simply return 'data' to perform no pre-processing
        """
        return data

    def get_cache_file_path(self):
        """
        An absolute, local, file path where this dataset is stored on disk.
        :return:
        """
        return self.get_cache_directory() + '/' + self.get_local_filename()

    def get_cache_directory(self):
        """
        Gets the directory where cache files are stored, typically the OS-provided "temp" directory.
        :return: The directory where cached files are stored
        """
        return tempfile.gettempdir()

    def read_cache(self):
        """
        Returns the requested dataset, downloading it and storing it in the cache if needed.

        :return: An absolute path to the data saved on the local filesystem
        """
        cache_file_path = self.get_cache_file_path()
        if self.get_remote_url() is None or os.path.exists(cache_file_path) and not self.__force_reload:
            return cache_file_path
        else:
            print("Downloading data from " + self.get_remote_url() + ". (It's going to space, give it a minute.)")
            self.__force_reload = False  # Do not download more than once, even when forced
            return self.load_cache(cache_file_path)

    def load_cache(self, cache_file_path):
        """
        Downloads the given URL and stores the data at the given file path.
        :param cache_file_path: The location on the filesystem where the data should be written
        :return: cache_file_path
        """
        cache_file = open(cache_file_path, 'w')
        data = urllib2.urlopen(self.get_remote_url())
        try:
            cache_file.write(self.preprocess(data.read()))
            print(cache_file)
        finally:
            cache_file.close()
        return cache_file_path

    def validate(self, csv):
        """
        Validates that the dataset contains all columns required by this analysis.

        Determines which columns are required by evaluating self for instance variables whose name starts with "ROW_".
        Subclasses should define an instance variable for every row in the dataset they expect to be consumed.

        :param csv: A CSV DictReader containing the loaded data
        :return: The CSV DictReader passed as an argument (for method chaining)
        """
        for required in self.required_rows():
            if required not in csv.fieldnames:
                raise Exception("Row missing from dataset: " + str(required) + " Available rows: " + str(csv.fieldnames))
        return csv

    def required_rows(self):
        required = []
        for row in self.__dict__.keys():
            if row.startswith("ROW_"):
                required.append(self.__dict__[row])
        return required


class Socioeconomic(DataSet):

    def __init__(self, force_reload=False):
        DataSet.__init__(self, force_reload)
        self.ROW_PERCENT_HOUSING_CROWDED = "PERCENT OF HOUSING CROWDED"
        self.ROW_PERCENT_HOUSEHOLDS_BELOW_POVERTY = "PERCENT HOUSEHOLDS BELOW POVERTY"
        self.ROW_PERCENT_16_UNEMPLOYED = "PERCENT AGED 16+ UNEMPLOYED"
        self.ROW_PERCENT_25_NO_DIPLOMA = "PERCENT AGED 25+ WITHOUT HIGH SCHOOL DIPLOMA"
        self.ROW_PERCENT_UNDER_18_OVER_64 = "PERCENT AGED UNDER 18 OR OVER 64"
        self.ROW_PER_CAPITA_INCOME = "PER CAPITA INCOME "       # src data contains trailing space
        self.ROW_HARDSHIP_INDEX = "HARDSHIP INDEX"
        self.ROW_COMMUNITY_NAME = "COMMUNITY AREA NAME"

    def get_remote_url(self):
        return "http://data.cityofchicago.org/api/views/kn9c-c2s2/rows.csv?accessType=DOWNLOAD&api_foundry=true"

    def get_local_filename(self):
        return "neighborhood_socioeconomic.csv"


class BusinessLicenses(DataSet):

    def __init__(self, force_reload=False):
        DataSet.__init__(self, force_reload)
        self.ROW_LICENSE_TERM_START_DATE = "LICENSE TERM START DATE"
        self.ROW_LICENSE_TERM_END_DATE = "LICENSE TERM EXPIRATION DATE"
        self.ROW_LICENSE_CODE = "LICENSE CODE"
        self.ROW_LICENSE_DESCRIPTION = "LICENSE DESCRIPTION"
        self.ROW_BUSINESS_ACTIVITY = "BUSINESS ACTIVITY"
        self.ROW_LATITUDE = "LATITUDE"
        self.ROW_LONGITUDE = "LONGITUDE"
        self.ROW_LICENSE_NUMBER = "LICENSE NUMBER"
        self.ROW_LICENSE_DESCRIPTION = "LICENSE DESCRIPTION"
        self.ROW_BUSINESS_DBA = "DOING BUSINESS AS NAME"
        self.ROW_BUSINESS_LEGAL_NAME = "LEGAL NAME"
        self.ROW_BUSINESS_CITY = "CITY"
        self.ROW_BUSINESS_ZIP = "ZIP CODE"
        self.ROW_BUSINESS_STATE = "STATE"
        self.ROW_BUSINESS_ADDRESS = "ADDRESS"

    def get_remote_url(self):
        return "http://data.cityofchicago.org/api/views/r5kz-chrr/rows.csv?accessType=DOWNLOAD&api_foundry=true"

    def get_local_filename(self):
        return "chicago_business_licenses.csv"


class CensusTracts(DataSet):

    def __init__(self, force_reload=False):
        DataSet.__init__(self, force_reload)
        self.ROW_GEOID = "GEOID"
        self.ROW_LATITUDE = "INTPTLAT"
        self.ROW_LONGITUDE = "INTPTLONG"
        self.ROW_POPULATION = "POP10"

    def preprocess(self, data):
        processed = str()

        # This bit of stupidity required to strip trailing whitespace from last column (and column header)
        for line in iter(data.splitlines()):
            processed += line.strip() + "\n"
        return processed

    def get_remote_url(self):
        return "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/census_tracts_list_17.txt"

    def get_local_filename(self):
        return "illinois_census_tracts.tsv"

    def as_dictionary(self):
        csv.register_dialect('CensusTSV', delimiter='\t', skipinitialspace=True, quoting=csv.QUOTE_NONE)
        return self.validate(csv.DictReader(open(self.read_cache(), 'rb'), dialect="CensusTSV"))


class Neighborhoods(DataSet):

    def __init__(self, force_reload=False):
        DataSet.__init__(self, force_reload)
        self.ROW_AREA_NUMBER = "AREA_NUMBE"
        self.ROW_AREA_NAME = "COMMUNITY"

    def get_remote_url(self):
        return "http://data.cityofchicago.org/api/views/igwz-8jzy/rows.csv?accessType=DOWNLOAD&api_foundry=true"

    def get_local_filename(self):
        return "chicago_neighborhoods.csv"


class NeighborhoodTractsMap(DataSet):

    def __init__(self):
        DataSet.__init__(self, False)
        self.ROW_AREA_NUMBER = "CHGOCA"
        self.ROW_TRACT_GEOID = "TRACT"

    def get_remote_url(self):
        return None

    def get_local_filename(self):
        return "census_tract_to_neighborhood.csv"

    def get_cache_directory(self):
        return os.path.dirname(os.path.abspath(__file__)) + "/data"
