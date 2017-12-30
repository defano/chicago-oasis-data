from oasis import data
import json


def write_license_index(output_dir):
    table = []
    for license_code in data.get_license_codes():
        description = data.get_license_description(license_code)
        year_range = data.get_license_date_range(license_code)

        table.append({
            "title": description,
            "label": description,
            "value": data.encode_license_description(description),
            "min-year": year_range[0],
            "max-year": year_range[1]
        })

    with open(output_dir + "/licenses.json", "w") as output_file:
        output_file.write(json.dumps(table, indent=2))
