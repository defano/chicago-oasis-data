#!/usr/bin/env python

import argparse
import oasis.data
import oasis.acessibility
import oasis.license_index
import oasis.socioeconomic
import oasis.critical_businesses

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                     description="""
Chicago Oasis Data Generator
    
Downloads required source data and calculates business accessibility, critical
business lists and socioeconomic information for census tracts and 
neighborhoods within the City of Chicago. 

See github.com/defano/chicago-oasis-data for more information.""")

    parser.add_argument('--access', action='store_true', dest='access', default=False,
                        help="generate only accessibility data")

    parser.add_argument('--critical', action='store_true', dest='critical', default=False,
                        help="generate only critical business data")

    parser.add_argument('--index', action='store_true', dest='index', default=False,
                        help="generate only licenses.json index")

    parser.add_argument('--socio', action='store_true', dest='demographic', default=False,
                        help="generate only socioeconomic.json data")

    parser.add_argument('--clean', action='store_true', dest='clean', default=False,
                        help="force download of all dependent datasets")

    parser.add_argument('--start-at', action='store', dest='start_at', default=None,
                        help="start generating at this license code (useful for restarting failed jobs")

    parser.add_argument('-lc', action='append', dest='licenses', default=[],
                        help="generate only this license code (e.g., 1472")

    parser.add_argument('-o', action='store', dest='output_dir', default="./",
                        help="path where output should be written (default is working directory")

    args = parser.parse_args()

    if args.licenses:
        print("Generating data only for license codes: " + str(args.licenses))
    else:
        print("Generating data for all licenses.")

    if args.start_at:
        print("Generating data starting at license code " + str(args.start_at))

    print("Writing output to " + args.output_dir)

    limited_datasets = args.critical or args.access or args.index or args.demographic

    if args.clean:
        print("Forcing download of all dependent data.")
        oasis.data.download_all()

    if not limited_datasets or args.index:
        print("Generating license index data.")
        oasis.license_index.write_license_index(args.output_dir)

    if not limited_datasets or args.demographic:
        print("Generating socioeconomic data.")
        oasis.socioeconomic.write_socioeconomics(args.output_dir)

    if not limited_datasets or args.critical:
        print("Generating critical business data.")
        oasis.critical_businesses.write_critical_businesses(args.output_dir, args.licenses, args.start_at)

    if not limited_datasets or args.access:
        print("Generating business accessibility data.")
        oasis.acessibility.write_accessibility_data(args.output_dir, args.licenses, args.start_at)


if __name__ == "__main__":
    main()
