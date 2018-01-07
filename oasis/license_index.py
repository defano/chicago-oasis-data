from oasis import data
import json


def produce_license_rpt(output_dir):
    table = []
    for license_code in data.get_license_codes():
        description = data.get_license_description(license_code)
        year_range = data.get_license_date_range(license_code)

        table.append({
            "title": description,
            "label": description,
            "value": data.get_license_file_key(description),
            "min-year": year_range[0],
            "max-year": year_range[1]
        })

    with open(output_dir + "/licenses.json", "w") as output_file:
        output_file.write(json.dumps(table, indent=2))
