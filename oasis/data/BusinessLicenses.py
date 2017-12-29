from oasis.data.DataSet import DataSet
import csv


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

    def get_remote_url(self):
        return "http://data.cityofchicago.org/api/views/r5kz-chrr/rows.csv?accessType=DOWNLOAD&api_foundry=true"

    def get_local_filename(self):
        return "chicago_business_licenses.csv"

    def get_dictionary(self):
        return self.validate(csv.DictReader(open(self.read_cache(), 'rb')))
