import oasis.data

def get_census_tract_ids():
    tracts = oasis.data.get_census_tracts_database()
    ids = set()
    for tract in tracts:
        ids.add(tract['GEOID'])
    return ids

def get_neighborhood_ids():
    neighborhoods = oasis.data.get_neighborhoods_database()
    ids = set()
    for neighborhood in neighborhoods:
        ids.add(neighborhood['AREA_NUMBE'])
    return ids


def get_census_tracts_in_neighborhood(community_number):
    mapping_data = oasis.data.get_census_neighborhood_map_database()
    tracts = list()
    for mapping in mapping_data:
        if community_number == mapping['CHGOCA']:
            tracts.append(mapping['TRACT'])
    return tracts


def get_census_centroid(geoid):
    tracts = oasis.data.get_census_tracts_database()
    for tract in tracts:
        if geoid_matches(geoid, tract['GEOID']):
            return float(tract['INTPTLAT']), float(tract['INTPTLONG'])


def geoid_matches(geo1, geo2):
    return geo1 in geo2 or geo2 in geo1
