import oasis.licenses
import oasis.geoareas
import oasis.gis

def calculate_accessibility():
    # license_types = oasis.licenses.get_license_types()
    #
    # # Walk each license type
    # for license_type in license_types:
    #     license_code = license_type[0]
        license_code = "1009"
        license_range = oasis.licenses.get_license_date_range(license_code)
        licenses = oasis.licenses.get_licenses(license_code)

        # Walk each year of available data
        for year in range(license_range[0].tm_year, license_range[1].tm_year):
            licenses_this_year = oasis.licenses.filter_by_year(licenses, year)

            # Walk each neighborhood
            for neighborhood in oasis.geoareas.get_neighborhood_ids():

                # Walk each census tract
                for tract in oasis.geoareas.get_census_tracts_in_neighborhood(neighborhood):
                    tract_centroid = oasis.geoareas.get_census_centroid(tract)
                    tract_lat = tract_centroid[0]
                    tract_lng = tract_centroid[1]

                    for license in licenses_this_year:
                        license_lat = license['LATITUDE']
                        license_lng = license['LONGITUDE']

                        print(license['DOING BUSINESS AS NAME'] + "->" + str(oasis.gis.distance_lat_lng(tract_lat, tract_lng, license_lat, license_lng, 'm')))


calculate_accessibility()