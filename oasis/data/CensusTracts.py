from oasis.data.DataSet import DataSet
import csv


class CensusTracts(DataSet):

    def __init__(self, force_reload=False):
        DataSet.__init__(self, force_reload)
        self.ROW_GEOID = "GEOID"
        self.ROW_LATITUDE = "INTPTLAT"
        self.ROW_LONGITUDE = "INTPTLONG"

    def preprocess_downloaded_file(self, data):
        processed = str()

        # This bit of stupidity required to strip trailing whitespace from last column (and column header)
        for line in iter(data.splitlines()):
            processed += line.strip() + "\n"
        return processed

    def get_remote_url(self):
        return "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/census_tracts_list_17.txt"

    def get_local_filename(self):
        return "illinois_census_tracts.tsv"

    def get_dictionary(self):
        csv.register_dialect('CensusTSV', delimiter='\t', skipinitialspace=True, quoting=csv.QUOTE_NONE)
        return self.validate(csv.DictReader(open(self.read_cache(), 'rb'), dialect="CensusTSV"))
