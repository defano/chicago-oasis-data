from oasis import data
import json


def produce_socioeconomic_rpt(output_dir):
    table = {}

    for neighborhood in data.socioeconomic_db.as_dictionary():
        name = neighborhood[data.socioeconomic_db.ROW_COMMUNITY_NAME].upper()

        if name.upper() != "CHICAGO":
            table[name] = {
                "PERCENT OF HOUSING CROWDED":
                    float(neighborhood[data.socioeconomic_db.ROW_PERCENT_HOUSING_CROWDED]),
                "PERCENT HOUSEHOLDS BELOW POVERTY":
                    float(neighborhood[data.socioeconomic_db.ROW_PERCENT_HOUSEHOLDS_BELOW_POVERTY]),
                "PERCENT AGED 16+ UNEMPLOYED":
                    float(neighborhood[data.socioeconomic_db.ROW_PERCENT_16_UNEMPLOYED]),
                "PERCENT AGED 25+ WITHOUT HIGH SCHOOL DIPLOMA":
                    float(neighborhood[data.socioeconomic_db.ROW_PERCENT_25_NO_DIPLOMA]),
                "PERCENT AGED UNDER 18 OR OVER 64":
                    float(neighborhood[data.socioeconomic_db.ROW_PERCENT_UNDER_18_OVER_64]),
                "PER CAPITA INCOME":
                    int(neighborhood[data.socioeconomic_db.ROW_PER_CAPITA_INCOME]),
                "HARDSHIP INDEX":
                    int(neighborhood[data.socioeconomic_db.ROW_HARDSHIP_INDEX])
            }

    with open(output_dir + "/socioeconomic.json", "w") as output_file:
        output_file.write(json.dumps(table, indent=2))
