import json
import math
import os.path
from oasis import data, gis, progress


class _AccessDatabase:

    def __init__(self):
        self.data = {}
        self.completed = set()

    def count_business(self, tract_id, neighborhood_id, tract_population, distance, year, license_code, license_record):

        license_number = license_record[data.license_db.ROW_LICENSE_NUMBER]
        license_desc = license_record[data.license_db.ROW_LICENSE_DESCRIPTION]

        if license_code not in self.data:
            self.data = {license_code: {}}

        if year not in self.data[license_code]:
            self.data[license_code][year] = {}

        if "TRACT" not in self.data[license_code][year]:
            self.data[license_code][year] = {"TRACT": {}, "HOOD": {}, "POP": {}}

        if tract_id not in self.data[license_code][year]['TRACT']:
            self.data[license_code][year]['TRACT'][tract_id] = _AreaRecord(tract_id, year, license_desc)
        self.data[license_code][year]['TRACT'][tract_id].count_business(license_number, distance)

        if neighborhood_id not in self.data[license_code][year]['HOOD']:
            self.data[license_code][year]['HOOD'][neighborhood_id] = _AreaRecord(neighborhood_id, year, license_desc)
        self.data[license_code][year]['HOOD'][neighborhood_id].count_business(license_number, distance)

        if distance <= 1.0:
            if license_number not in self.data[license_code][year]['POP']:
                self.data[license_code][year]['POP'][license_number] = _ServedAreaRecord(license_number)
            self.data[license_code][year]['POP'][license_number].count_pop(tract_population)

    def get_license_codes(self):
        return self.data.keys()

    def get_years_for_license_code(self, license_code):
        if license_code in self.data:
            return self.data[license_code].keys()
        else:
            return []

    def get_census_records_json(self, license_code, year):
        return json.dumps(self.get_census_records(license_code, year).values(), cls=_CensusRecordJsonEncoder, indent=2)

    def get_census_records(self, license_code, year):
        return self.data[license_code][year]['TRACT']

    def get_neighborhood_records(self, license_code, year):
        return self.data[license_code][year]['HOOD']

    def get_neighborhood_records_json(self, license_code, year):
        return json.dumps(self.get_neighborhood_records(license_code, year).values(),
                          cls=_NeighborhoodRecordJsonEncoder, indent=2)

    def get_served_population(self, license_code, license_number, year):
        return self.data[license_code][year]['POP'][license_number].pop

    def get_critical_businesses(self, license_code, year):
        critical_businesses = set()
        census_records = self.get_census_records(license_code, year)
        for tract in census_records:
            if len(census_records[tract].nearby_businesses) == 1:
                license_number = census_records[tract].nearby_businesses[0]
                critical_businesses.add(
                    _CriticalBusinessRecord(license_code, license_number, year,
                                            self.get_served_population(license_code, license_number, year)))

        return list(critical_businesses)

    def get_critical_businesses_json(self, license_code, year):
        return json.dumps(self.get_critical_businesses(license_code, year),
                          cls=_CriticalBusinessRecordJsonEncoder, indent=2)


class _CriticalBusinessRecord:
    """
    A record of a "critical business" (that is, the only business within a mile of a given population)
    """
    def __init__(self, license_code, license_number, year, at_risk_pop):
        self.license_code = license_code
        self.license_number = license_number
        self.license_desc = data.get_license_description(license_code)
        self.year = year
        self.at_risk_pop = at_risk_pop
        self.dba = data.get_business_dba(license_number)
        self.legal_name = data.get_business_legal_name(license_number)
        self.lat_lng = data.get_business_lat_lng(license_number)
        self.address = data.get_business_address(license_number)
        self.city = data.get_business_city(license_number)
        self.state = data.get_business_state(license_number)
        self.zip = data.get_business_zip(license_number)

    def __hash__(self):
        return hash(str(str(self.lat_lng[0]) + str(self.lat_lng[1])))

    def __eq__(self, other):
        return hash(self) == hash(other)


class _ServedAreaRecord:
    """
    A record of the population within one mile's distance of a given business.
    """
    def __init__(self, license_number):
        self.license_number = license_number
        self.pop = 0

    def count_pop(self, pop):
        if pop:
            self.pop += int(pop)


class _AreaRecord:
    """
    A record of the number of businesses of a given license type within three miles of a given geographic area.
    """
    def __init__(self, area, year, license_desc):
        """
        :param area: The geographic area (neighborhood name or census tract ID) this record applies to (i.e., "OHARE"
        or "510123")
        :param year: The calendar year this data applies to
        :param license_desc: The description of the type of license (i.e., "Music and Dance")
        """
        self.one_mile = 0
        self.two_mile = 0
        self.three_mile = 0
        self.access1 = 0
        self.access2 = 0
        self.area = area
        self.year = year
        self.business_type = license_desc
        self.nearby_businesses = []

    def count_business(self, license_number, distance):
        self.access2 += 1.0 / math.pow(distance, 2)
        self.access1 += 1.0 / distance
        if distance <= 1.0:
            self.one_mile += 1
            self.nearby_businesses.append(license_number)

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


class _CriticalBusinessRecordJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, _CriticalBusinessRecord):
            return {"STATE": o.state,
                    "ZIP": int(o.zip),
                    "LATTITUDE": float(o.lat_lng[0]),      # sic; 'LATTITUDE' is misspelled in API :(
                    "LONGITUDE": float(o.lat_lng[1]),
                    "ADDRESS": o.address,
                    "YEAR": int(o.year),
                    "DOING_BUSINESS_AS_NAME": o.dba,
                    "POP_AT_RISK": int(o.at_risk_pop),
                    "BUSINESS_TYPE": o.license_desc,
                    "LEGAL_NAME": o.legal_name
                    }

        return super(_CriticalBusinessRecordJsonEncoder, self).default(o)


class _NeighborhoodRecordJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, _AreaRecord):
            return {"BUSINESS_TYPE": o.business_type,
                    "COMMUNITY_AREA": o.area,
                    "YEAR": o.year,
                    "ACCESS1": o.access1,
                    "ACCESS2": o.access2}

        return super(_NeighborhoodRecordJsonEncoder, self).default(o)


class _CensusRecordJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, _AreaRecord):
            return {"BUSINESS_TYPE": o.business_type,
                    "TRACT": o.get_tract10(),
                    "YEAR": o.year,
                    "ONE_MILE": o.one_mile,
                    "TWO_MILE": o.two_mile,
                    "THREE_MILE": o.three_mile,
                    "ACCESS1": o.access1,
                    "ACCESS2": o.access2}

        return super(_CensusRecordJsonEncoder, self).default(o)


def produce_accessibility_rpt(output_dir, critical_dir, census_dir, community_dir, license_codes, start_at):

    # Get set all of business license types issued by Chicago
    if not license_codes:
        license_codes = data.get_license_codes()

    overall_progress = progress.Progress(len(license_codes))

    # Walk each unique license type
    for license_code in license_codes:
        database = _AccessDatabase()

        if start_at is not None and int(start_at) > int(license_code):
            print("Skipping license code " + license_code + " (starting at " + str(start_at) + ")")
            continue
        else:
            start_at = None

        license_desc = None
        licenses = data.get_licenses(license_code)
        licenses_count = len(licenses)

        license_progress = progress.Progress(licenses_count)
        print("Crunching data for license code " + str(license_code) + " (" + data.get_license_description(license_code)
              + " - " + str(licenses_count) + " license records)")

        # Walk each business license of this category
        for license in licenses:
            license_number = license[data.license_db.ROW_LICENSE_NUMBER]
            license_start, license_end = data.get_business_years(license_number)

            # Ignore licenses with bogus start or end dates
            if license_start is None or license_end is None:
                continue

            license_lat, license_lng = license[data.license_db.ROW_LATITUDE], license[data.license_db.ROW_LONGITUDE]
            license_desc = license[data.license_db.ROW_LICENSE_DESCRIPTION]

            # Walk each neighborhood
            for neighborhood_id in data.get_neighborhood_ids():
                neighborhood_name = data.get_neighborhood_name(neighborhood_id)

                # Walk each census tract in the neighborhood
                for tract_id in data.get_census_tracts_in_neighborhood(neighborhood_id):
                    tract_centroid = data.get_census_centroid(tract_id)
                    tract_population = data.get_census_population(tract_id)

                    # Ignore records missing geo-location data
                    if license_lat and license_lng and tract_centroid[0] and tract_centroid[1]:
                        # Calculate the distance between this business and the center of this census tract
                        distance = gis.distance_lat_lng(license_lat, license_lng, tract_centroid[0], tract_centroid[1])

                        # Count this business in each year the license was active
                        for year in range(license_start, license_end + 1):
                            database.count_business(tract_id, neighborhood_name, tract_population, distance, year,
                                                    license_code, license)

            license_progress.report()

        overall_progress.report("Overall progress: %s%% complete.\n")

        # Dump this result-set to disk
        _dump_access(database, license_code, license_desc, output_dir, census_dir, community_dir)
        _dump_critical(database, license_code, license_desc, output_dir, critical_dir)

        del database        # Try to convince Python to free our last result set


def _dump_critical(database, license_code, license_desc, output_dir, critical_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if not os.path.exists(output_dir + "/" + critical_dir):
        os.makedirs(output_dir + "/" + critical_dir)

    for year in database.get_years_for_license_code(license_code):
        filename = "critical-" + data.get_license_key(license_desc) + "-" + str(year) + ".json"
        with open(output_dir + "/" + critical_dir + "/" + filename, "w") as critical_file:
            critical_file.write(database.get_critical_businesses_json(license_code, year))


def _dump_access(database, license_code, license_desc, output_dir, census_dir, community_dir):

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if not os.path.exists(output_dir + "/" + census_dir):
        os.makedirs(output_dir + "/" + census_dir)
    if not os.path.exists(output_dir + "/" + community_dir):
        os.makedirs(output_dir + "/" + community_dir)

    for year in database.get_years_for_license_code(license_code):
        filename = data.get_license_key(license_desc) + "-" + str(year) + ".json"
        with open(output_dir + "/" + census_dir + "/" + filename, "w") as census_file:
            census_file.write(database.get_census_records_json(license_code, year))
        with open(output_dir + "/" + community_dir + "/" + filename, "w") as community_file:
            community_file.write(database.get_neighborhood_records_json(license_code, year))

