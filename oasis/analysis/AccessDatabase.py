import math
import json


class AccessDatabase:

    def __init__(self):
        self.license_codes = {}
        self.completed = set()
        self.license_descriptions = {}

    def increment(self, business_type, tract_id, neighborhood_id, distance, license_code, license_number, year):

        tract_hash = str((tract_id, license_code, license_number, year))
        neighborhood_hash = str((neighborhood_id, license_code, license_number, year))

        if license_code not in self.license_codes:
            self.license_codes = {license_code: {}}

        if year not in self.license_codes[license_code]:
            self.license_codes[license_code][year] = {}

        if "t" not in self.license_codes[license_code][year] or "n" not in self.license_codes[license_code][year]:
            self.license_codes[license_code][year] = {"t": {}, "n": {}}

        if tract_hash not in self.completed:
            if tract_id in self.license_codes[license_code][year]['t']:
                self.license_codes[license_code][year]['t'][tract_id].increment(distance)
            else:
                self.license_codes[license_code][year]['t'][tract_id] = AccessRecord(tract_id, year, business_type)
                self.license_codes[license_code][year]['t'][tract_id].increment(distance)

        if neighborhood_hash not in self.completed:
            if neighborhood_id in self.license_codes[license_code][year]['n']:
                self.license_codes[license_code][year]['n'][neighborhood_id].increment(distance)
            else:
                self.license_codes[license_code][year]['n'][neighborhood_id] = AccessRecord(tract_id, year,
                                                                                            business_type)
                self.license_codes[license_code][year]['n'][neighborhood_id].increment(distance)

        # Don't process duplicates in the same year
        self.completed.add(tract_hash)
        self.completed.add(neighborhood_hash)

    def get_description_for_license_code(self, license_code):
        return self.license_descriptions[license_code]

    def get_license_codes(self):
        return self.license_codes.keys()

    def get_years_for_license_code(self, license_code):
        return self.license_codes[license_code].keys()

    def get_census_records_json(self, license_code, year):
        return json.dumps(self.get_census_records(license_code, year).values(), cls=AccessRecordJsonEncoder, indent=2)

    def get_census_records(self, license_code, year):
        return self.license_codes[license_code][year]['t']

    def get_neighborhood_records(self, license_code, year):
        return self.license_codes[license_code][year]['n']


class AccessRecord:

    def __init__(self, tract, year, business_type):
        self.one_mile = 0
        self.two_mile = 0
        self.three_mile = 0
        self.access1 = 0
        self.access2 = 0
        self.tract = tract
        self.year = year
        self.business_type = business_type

    def increment(self, distance):
        self.access2 += 1.0 / math.pow(distance, 2)
        self.access1 += 1.0 / distance
        if distance <= 1.0:
            self.one_mile += 1
        if distance <= 2.0:
            self.two_mile += 1
        if distance <= 3.0:
            self.three_mile += 1

    def get_tract10(self):
        if len(self.tract) > 4 and self.tract.endswith("00"):
            return self.tract[:-2]
        elif len(self.tract) > 4:
            return self.tract[0:4] + "." + self.tract[-2:]
        else:
            return self.tract


class AccessRecordJsonEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, AccessRecord):
            return {"BUSINESS_TYPE": o.business_type,
                    "TRACT": o.get_tract10(),
                    "YEAR": o.year,
                    "ONE_MILE": o.one_mile,
                    "TWO_MILE": o.two_mile,
                    "THREE_MILE": o.three_mile,
                    "ACCESS1": o.access1,
                    "ACCESS2": o.access2}

        return super(AccessRecordJsonEncoder, self).default(o)
