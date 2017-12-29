from oasis.data.DataSet import DataSet
import csv


class Neighborhoods(DataSet):

    def __init__(self, force_reload=False):
        DataSet.__init__(self, force_reload)
        self.ROW_AREA_NUMBER = "AREA_NUMBE"

    def get_remote_url(self):
        return "http://data.cityofchicago.org/api/views/igwz-8jzy/rows.csv?accessType=DOWNLOAD&api_foundry=true"

    def get_local_filename(self):
        return "chicago_neighborhoods.csv"

    def get_dictionary(self):
        return self.validate(csv.DictReader(open(self.read_cache(), 'rb')))
