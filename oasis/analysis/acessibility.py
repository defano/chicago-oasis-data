from oasis.data import data
from oasis import gis
from oasis.analysis.AccessDatabase import AccessDatabase

database = AccessDatabase()


def calculate_accessibility():
    license_types = data.get_license_types()
    # license_types = [("1472", "blah", "blah")]

    # Walk each unique license type
    for license_type in license_types:
        print("Crunching data for license " + str(license_type))
        license_code = license_type[0]
        licenses = data.get_licenses(license_code)

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
            for community_area_number in data.get_neighborhood_ids():

                # Walk each census tract in the neighborhood
                for tract in data.get_census_tracts_in_neighborhood(community_area_number):
                    tract_centroid = data.get_census_centroid(tract)

                    try:
                        distance = gis.distance_lat_lng(license_lat, license_lng, tract_centroid[0], tract_centroid[1])
                    except ValueError:
                        continue

                    # Increment the data for each year this license was active
                    for year in range(license_start, license_end + 1):
                        database.increment(license_desc, tract, community_area_number, distance, license_code, license_number, year)


# TODO
# def generate_output(output_dir):
#     if not os.path.exists(output_dir):
#         os.makedirs(output_dir)
#     if not os.path.exists(output_dir + "/census"):
#         os.makedirs(output_dir + "/census")
#     if not os.path.exists(output_dir + "/community"):
#         os.makedirs(output_dir + "/community")
#
#     calculate_accessibility()
#     for license_code in database.get_license_codes():
#         for year in database.get_years_for_license_code(license_code):
#             pass
#
# calculate_accessibility()
# print database.get_census_records_json("1472", 2015)

