from oasis.data.DataSet import DataSet
import csv


class NeighborhoodTractsMap(DataSet):

    def __init__(self, force_reload=False):
        DataSet.__init__(self, force_reload)
        self.ROW_AREA_NUMBER = "CHGOCA"
        self.ROW_TRACT_GEOID = "TRACT"

    def get_remote_url(self):
        raise Exception("This data source is local to the project and has no remote resource.")

    def get_local_filename(self):
        return "census_tract_to_neighborhood.csv"

    def get_dictionary(self):
        return self.validate(csv.DictReader(open(self.read_cache(), 'rb')))

    def get_cache_directory(self):
        return "../data"
