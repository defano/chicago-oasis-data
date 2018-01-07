import json
import math
import os.path
from oasis import data, gis, progress


class _Analysis:
    """
    An in-memory "database" of analysis records. Aggregates accessibility information on a per license and year basis.
    """

    TRACT_KEY = "t"
    NEIGHBORHOOD_KEY = 'h'
    POPULATION_KEY = 'p'

    def __init__(self):
        self.data = {}
        self.completed = set()

    def count_business(self, tract_id, neighborhood_id, tract_population, distance, year, license_code, license_record):
        """
        Update analysis with information from a given business license record.

        This method should be invoked for every row in the license table, crossed with every census tract, crossed with
        every year the license record applies. Thus, in performing a full analysis, this method will get called
        approximately 1.6 billion times... ~1M license rows x ~2 years per record (on avg) x ~800 census tracts in
        Chicago.

        Note that this method DOES NOT filter duplicates. It is the responsibility of the caller to assure the same
        business is not being counted twice in the same year or census tract.

        :param tract_id: The census tract ID where this business is located
        :param neighborhood_id: The name of the neighborhood where the business is located
        :param tract_population: The population of this census tract
        :param distance: The distance (in miles) of the business from the given census tract
        :param year: The calendar year in which this license record is valid (i.e., 2017)
        :param license_code: The numeric license code which identifies the business category (i.e., 1004)
        :param license_record: A dictionary containing all of the "rows" of this license record.
        :return: Nada
        """
        license_number = license_record[data.license_db.ROW_LICENSE_NUMBER]
        license_desc = license_record[data.license_db.ROW_LICENSE_DESCRIPTION]

        if license_code not in self.data:
            self.data = {license_code: {}}

        if year not in self.data[license_code]:
            self.data[license_code][year] = {}

        if _Analysis.TRACT_KEY not in self.data[license_code][year]:
            self.data[license_code][year] = {_Analysis.TRACT_KEY: {},
                                             _Analysis.NEIGHBORHOOD_KEY: {},
                                             _Analysis.POPULATION_KEY: {}}

        if tract_id not in self.data[license_code][year][_Analysis.TRACT_KEY]:
            self.data[license_code][year][_Analysis.TRACT_KEY][tract_id] = _AreaRecord(tract_id, year, license_desc)
        self.data[license_code][year][_Analysis.TRACT_KEY][tract_id].count_business(license_number, distance)

        if neighborhood_id not in self.data[license_code][year][_Analysis.NEIGHBORHOOD_KEY]:
            self.data[license_code][year][_Analysis.NEIGHBORHOOD_KEY][neighborhood_id] = \
                _AreaRecord(neighborhood_id, year, license_desc)

        self.data[license_code][year][_Analysis.NEIGHBORHOOD_KEY][neighborhood_id]\
            .count_business(license_number, distance)

        if distance <= 1.0:
            if license_number not in self.data[license_code][year][_Analysis.POPULATION_KEY]:
                self.data[license_code][year][_Analysis.POPULATION_KEY][license_number] = \
                    _ServedAreaRecord(license_number)
            self.data[license_code][year][_Analysis.POPULATION_KEY][license_number].count_pop(tract_population)

    def get_analyzed_license_codes(self):
        """
        Gets a set of unique license codes present in the analysis.
        :return: The license keys
        """
        return self.data.keys()

    def get_analyzed_years_for_license_code(self, license_code):
        """
        Gets a set of unique years for analysis data was collected for licenses of the given license code.
        :param license_code: The license code (i.e., 1004) whose data should be retrieved
        :return: The set of years for which data for the given license code was collected, or the empty list if no
        data is available.
        """
        if license_code in self.data:
            return self.data[license_code].keys()
        else:
            return []

    def get_analyzed_census_records_json(self, license_code, year):
        """
        Returns a JSON-formatted string containing an array of census-level accessibility records for the given year
        and license code. This data is suitable for writing to result files in the 'census/' directory.
        :param license_code: The numeric license code
        :param year: The year
        :return: A JSON-formatted string
        """
        return json.dumps(self.get_analyzed_census_records(license_code, year).values(),
                          cls=_CensusRecordJsonEncoder, indent=2)

    def get_analyzed_census_records(self, license_code, year):
        """
        Gets a map of tract_id to _AreaRecord (representing the aggregated accessibility data for the given license code
        and year)
        :param license_code: The license code whose data should be returned
        :param year: The year for which data should be returned
        :return: A map of tract_id -> _AreaRecord
        """
        return self.data[license_code][year][_Analysis.TRACT_KEY]

    def get_neighborhood_records(self, license_code, year):
        """
        Gets a map of neighborhood_id to _AreaRecord (representing the aggregated accessibility data for the given
        license code and year)
        :param license_code: The license code whose data should be returned
        :param year: The year for which data should be returned
        :return: A map of neighborhood_id -> _AreaRecord
        """
        return self.data[license_code][year][_Analysis.NEIGHBORHOOD_KEY]

    def get_neighborhood_records_json(self, license_code, year):
        """
        Returns a JSON-formatted string containing an array of neighborhood-level accessibility records for the given
        year and license code. This data is suitable for writing to result files in the 'community/' directory.
        :param license_code: The numeric license code
        :param year: The year
        :return: A JSON-formatted string
        """
        return json.dumps(self.get_neighborhood_records(license_code, year).values(),
                          cls=_NeighborhoodRecordJsonEncoder, indent=2)

    def get_served_population(self, license_code, license_number, year):
        """
        Returns the population living within one mile of the business identified by license code and license number.
        :param license_code: The license code of the business
        :param license_number: The license number of the business
        :param year: The year for which data should be retrieved
        :return: The population within one mile of the business
        """
        return self.data[license_code][year][_Analysis.POPULATION_KEY][license_number].pop

    def get_critical_businesses(self, license_code, year):
        """
        Returns a list of _CriticalBusinessRecord identifying all the critical businesses of a given license type
        :param license_code: The license code of businesses to be returned
        :param year: The year for which data should be returned
        :return: A list of zero or more _CriticalBusinessRecord objects
        """
        critical_businesses = set()
        census_records = self.get_analyzed_census_records(license_code, year)
        for tract in census_records:
            if len(census_records[tract].nearby_businesses) == 1:
                license_number = census_records[tract].nearby_businesses[0]
                critical_businesses.add(
                    _CriticalBusinessRecord(license_code, license_number, year,
                                            self.get_served_population(license_code, license_number, year)))

        return list(critical_businesses)

    def get_critical_businesses_json(self, license_code, year):
        """
        Returns a JSON-formatted string containing an array of critical business records for the given year and license
        code. This data is suitable for writing to result files in the 'critical/' directory.
        :param license_code: The numeric license code
        :param year: The year
        :return: A JSON-formatted string
        """
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
        """
        Updates this analysis record with information about a new business.
        :param license_number: The license number of the business
        :param distance: The distance (in miles) from the centroid of the analyzed area
        :return: None
        """
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
        """
        Converts a six-digit census tract identifier (i.e., 061037) to the "tract-10" representation (610.37)
        :return: The tract-10 representation of this record's census tract_id
        """
        if len(self.area) > 4 and self.area.endswith("00"):
            return self.area[:-2]
        elif len(self.area) > 4:
            return self.area[0:4] + "." + self.area[-2:]
        else:
            return self.area


class _CriticalBusinessRecordJsonEncoder(json.JSONEncoder):
    """
    Encodes _CriticalBusinessRecord objects in JSON conforming to the Chicago Oasis API.
    """
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
    """
    Encodes an _AreaRecord representing a neighborhood in JSON conforming to the Chicago Oasis API.
    """
    def default(self, o):
        if isinstance(o, _AreaRecord):
            return {"BUSINESS_TYPE": o.business_type,
                    "COMMUNITY_AREA": o.area,
                    "YEAR": o.year,
                    "ACCESS1": o.access1,
                    "ACCESS2": o.access2}

        return super(_NeighborhoodRecordJsonEncoder, self).default(o)


class _CensusRecordJsonEncoder(json.JSONEncoder):
    """
    Encodes an _AreaRecord representating a census tract in JSON conforming to the Chicago Oasis API.
    """
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
    """
    Performs an accessibility analysis of Chicago business licenses, writing data incrementally to output files.
    :param output_dir: The path to output directory ('./' by default)
    :param critical_dir: The name of the directory where critical business data is written ('critical/' by default)
    :param census_dir: The name of the directory where census-level accessibility data is written ('/census' by default)
    :param community_dir: The name of the directory where neighborhood-level data is written ('community/' by default)
    :param license_codes: A list of license codes to be analyzed; empty indicates all available licenses.
    :param start_at: Start analysis at this code; analyses run in numerical order
    :return: None
    """

    # Get the set of all business license categories issued by Chicago
    if not license_codes:
        license_codes = data.get_license_codes()

    overall_progress = progress.Progress(len(license_codes))

    # Walk each unique license type
    for license_code in license_codes:
        database = _Analysis()

        # When user has requested restarting analysis at specific code, skip ahead...
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

        del database        # Try to convince Python to free our last result set (they're memory hogs)


def _dump_critical(database, license_code, license_desc, output_dir, critical_dir):
    """
    Writes critical business data to disk.
    :param database: The _Analysis object containing data to write
    :param license_code: The license code of the data to write
    :param license_desc: The license code description of the data to write (determines file names)
    :param output_dir: The base output directory to write
    :param critical_dir: The name of the directory in the output directory to write
    :return: None
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if not os.path.exists(output_dir + "/" + critical_dir):
        os.makedirs(output_dir + "/" + critical_dir)
    for year in database.get_analyzed_years_for_license_code(license_code):
        filename = "critical-" + data.get_license_file_key(license_desc) + "-" + str(year) + ".json"
        with open(output_dir + "/" + critical_dir + "/" + filename, "w") as critical_file:
            critical_file.write(database.get_critical_businesses_json(license_code, year))


def _dump_access(database, license_code, license_desc, output_dir, census_dir, community_dir):
    """
    Writes neighborhood and census-level accessibility to disk.
    :param database: The _Analysis object containing data to write
    :param license_code: The license code of the data to write
    :param license_desc: The license code description of the data to write (determines file names)
    :param output_dir: The base output directory to write
    :param census_dir: The name of the census directory to write to
    :param community_dir: The name of the community directory to write to
    :return: None
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if not os.path.exists(output_dir + "/" + census_dir):
        os.makedirs(output_dir + "/" + census_dir)
    if not os.path.exists(output_dir + "/" + community_dir):
        os.makedirs(output_dir + "/" + community_dir)
    for year in database.get_analyzed_years_for_license_code(license_code):
        filename = data.get_license_file_key(license_desc) + "-" + str(year) + ".json"
        with open(output_dir + "/" + census_dir + "/" + filename, "w") as census_file:
            census_file.write(database.get_analyzed_census_records_json(license_code, year))
        with open(output_dir + "/" + community_dir + "/" + filename, "w") as community_file:
            community_file.write(database.get_neighborhood_records_json(license_code, year))
