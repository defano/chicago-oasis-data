import json

import math

from oasis import data, gis, progress
import os.path


class _AccessDatabase:

    def __init__(self):
        self.data = {}
        self.completed = set()

    def count_business(self, business_type, tract_id, neighborhood_id, distance, license_code, license_number, year):

        # Some business licenses have database records that overlap years; prevent these overlaps from double-counting
        # the business
        record_hash = str((tract_id, license_code, license_number, year))

        if license_code not in self.data:
            self.data = {license_code: {}}

        if year not in self.data[license_code]:
            self.data[license_code][year] = {}

        if "t" not in self.data[license_code][year] or "n" not in self.data[license_code][year]:
            self.data[license_code][year] = {"t": {}, "n": {}}

        if record_hash not in self.completed:
            if tract_id in self.data[license_code][year]['t']:
                self.data[license_code][year]['t'][tract_id].count_business(distance)
            else:
                self.data[license_code][year]['t'][tract_id] = _AccessRecord(tract_id, year, business_type)
                self.data[license_code][year]['t'][tract_id].count_business(distance)

            if neighborhood_id in self.data[license_code][year]['n']:
                self.data[license_code][year]['n'][neighborhood_id].count_business(distance)
            else:
                self.data[license_code][year]['n'][neighborhood_id] = _AccessRecord(neighborhood_id, year, business_type)
                self.data[license_code][year]['n'][neighborhood_id].count_business(distance)

        # Don't process duplicates in the same year
        self.completed.add(record_hash)

    def get_license_codes(self):
        return self.data.keys()

    def get_years_for_license_code(self, license_code):
        return self.data[license_code].keys()

    def get_census_records_json(self, license_code, year):
        return json.dumps(
            self.get_census_records(license_code, year).values(),
            cls=_CensusRecordJsonEncoder,
            indent=2)

    def get_census_records(self, license_code, year):
        return self.data[license_code][year]['t']

    def get_neighborhood_records(self, license_code, year):
        return self.data[license_code][year]['n']

    def get_neighborhood_records_json(self, license_code, year):
        return json.dumps(
            self.get_neighborhood_records(license_code, year).values(),
            cls=_NeighborhoodRecordJsonEncoder,
            indent=2)


class _AccessRecord:
    def __init__(self, area, year, business_type):
        self.one_mile = 0
        self.two_mile = 0
        self.three_mile = 0
        self.access1 = 0
        self.access2 = 0
        self.area = area
        self.year = year
        self.business_type = business_type

    def count_business(self, distance):
        self.access2 += 1.0 / math.pow(distance, 2)
        self.access1 += 1.0 / distance
        if distance <= 1.0:
            self.one_mile += 1
        if distance <= 2.0:
            self.two_mile += 1
        if distance <= 3.0:
            self.three_mile += 1

    def get_tract10(self):
        if len(self.area) > 4 and self.area.endswith("00"):
            return self.area[:-2]
        elif len(self.area) > 4:
            return self.area[0:4] + "." + self.area[-2:]
        else:
            return self.area


class _NeighborhoodRecordJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, _AccessRecord):
            return {"BUSINESS_TYPE": o.business_type,
                    "COMMUNITY_AREA": o.area,
                    "YEAR": o.year,
                    "ACCESS1": o.access1,
                    "ACCESS2": o.access2}

        return super(_NeighborhoodRecordJsonEncoder, self).default(o)


class _CensusRecordJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, _AccessRecord):
            return {"BUSINESS_TYPE": o.business_type,
                    "TRACT": o.get_tract10(),
                    "YEAR": o.year,
                    "ONE_MILE": o.one_mile,
                    "TWO_MILE": o.two_mile,
                    "THREE_MILE": o.three_mile,
                    "ACCESS1": o.access1,
                    "ACCESS2": o.access2}

        return super(_CensusRecordJsonEncoder, self).default(o)


def write_accessibility_data(output_dir, license_codes, start_at):

    # Get set all of business license types issued by Chicago
    if not license_codes:
        license_codes = data.get_license_codes()

    overall_progress = progress.Progress(len(license_codes))

    # Walk each unique license type
    for license_code in license_codes:

        database = _AccessDatabase()

        if start_at is not None and start_at != license_code:
            print("Skipping license code " + license_code + " (starting at " + str(start_at) + ")")
            continue
        else:
            start_at = None

        license_desc = None
        licenses = data.get_licenses(license_code)
        licenses_count = len(licenses)

        print("Crunching data for license " + str(license_code) + " (" + str(licenses_count) + " records)")
        license_progress = progress.Progress(licenses_count)

        # Walk each business license of this category
        for license in licenses:
            license_lat = license[data.business_licenses_db.ROW_LATITUDE]
            license_lng = license[data.business_licenses_db.ROW_LONGITUDE]
            license_number = license[data.business_licenses_db.ROW_LICENSE_NUMBER]
            license_desc = license[data.business_licenses_db.ROW_LICENSE_DESCRIPTION]
            license_start, license_end = data.get_license_years(license)

            # Ignore licenses with bogus start or end dates
            if license_start is None or license_end is None:
                continue

            # Walk each neighborhood
            for neighborhood_id in data.get_neighborhood_ids():
                neighborhood_name = data.get_neighborhood_name(neighborhood_id)

                # Walk each census tract in the neighborhood
                for tract in data.get_census_tracts_in_neighborhood(neighborhood_id):
                    tract_centroid = data.get_census_centroid(tract)

                    # Calculate the distance between this business and the center of this census tract
                    try:
                        distance = gis.distance_lat_lng(license_lat, license_lng, tract_centroid[0], tract_centroid[1])
                    except ValueError:
                        continue

                    # Count this business in each year the license was active
                    for year in range(license_start, license_end + 1):
                        database.count_business(license_desc, tract, neighborhood_name, distance, license_code,
                                                license_number, year)

            license_progress.report()

        overall_progress.report("Overall %s%% complete.")
        _write_data(database, license_code, license_desc, output_dir)

        global database
        database = _AccessDatabase()


def _write_data(database, license_code, license_desc, output_dir):

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if not os.path.exists(output_dir + "/census"):
        os.makedirs(output_dir + "/census")
    if not os.path.exists(output_dir + "/community"):
        os.makedirs(output_dir + "/community")

    for year in database.get_years_for_license_code(license_code):
        filename = data.encode_license_description(license_desc) + "-" + str(year) + ".json"
        with open(output_dir + "/census/" + filename, "w") as output_file:
            output_file.write(database.get_census_records_json(license_code, year))
        with open(output_dir + "/community/" + filename, "w") as output_file:
            output_file.write(database.get_neighborhood_records_json(license_code, year))

