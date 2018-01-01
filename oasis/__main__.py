#!/usr/bin/env python

import argparse
import oasis.data
import oasis.analysis
import oasis.license_index
import oasis.socioeconomic


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                     description="""
Chicago Oasis Data Generator
    
Downloads required source data and calculates business accessibility, critical
business lists and socioeconomic information for census tracts and 
neighborhoods within the City of Chicago. 

See github.com/defano/chicago-oasis-data for more information.""")

    parser.add_argument('-lc', action='append', dest='licenses', default=[],
                        help="analyze only this license code (e.g., 1472)")

    parser.add_argument('-o', action='store', dest='output_dir', default="./",
                        help="path where output should be written (default is working directory)")

    parser.add_argument('--analysis', action='store_true', dest='analysis', default=False,
                        help="generate only accessibility and critical business analysis data")

    parser.add_argument('--index', action='store_true', dest='index', default=False,
                        help="generate only licenses.json index")

    parser.add_argument('--socio', action='store_true', dest='demographic', default=False,
                        help="generate only socioeconomic.json data")

    parser.add_argument('--clean', action='store_true', dest='clean', default=False,
                        help="force download of all dependent datasets")

    parser.add_argument('--start-at', action='store', dest='start_at', default=None,
                        help="start analysis at this license code (useful for restarting failed jobs")

    parser.add_argument('--community', action='store', dest='cmty', default="community",
                        help="directory where neighborhood data should be written (default is 'community')")

    parser.add_argument('--census', action='store', dest='census', default="census",
                        help="directory where census data should be written (default is 'census')")

    parser.add_argument('--critical', action='store', dest='critical', default="critical",
                        help="directory where critical business data should be written (default is 'critical')")

    args = parser.parse_args()

    if args.licenses:
        print("Analyzing only license codes: " + str(args.licenses))
    else:
        print("Analyzing data for all licenses.")

    if args.start_at:
        print("Analyzing data starting at license code " + str(args.start_at))

    print("Writing output to " + args.output_dir)

    if args.clean:
        print("Forcing download of all dependent data...")
        oasis.data.download_all()

    oasis.data.initialize_license_cache()
    limited_datasets = args.analysis or args.index or args.demographic

    if not limited_datasets or args.index:
        print("Generating license index data...")
        oasis.license_index.produce_license_rpt(args.output_dir)

    if not limited_datasets or args.demographic:
        print("Generating socioeconomic report...")
        oasis.socioeconomic.produce_socioeconomic_rpt(args.output_dir)

    if not limited_datasets or args.analysis:
        print("Performing analysis of business accessibility...")
        oasis.analysis.produce_accessibility_rpt(args.output_dir, args.critical, args.census, args.cmty, args.licenses,
                                                 args.start_at)


if __name__ == "__main__":
    main()
