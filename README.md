# Chicago Oasis Data

Dataset generator for the Chicago Oasis project. Downloads and analyzes neighborhood, census, demographic and business data within the City of Chicago. It produces a large file-set intended to be served to visualization clients via the [Chicago Oasis](https://github.com/defano/chicago-oasis) web app.

Based on Ben Galewsky's original [Apache Pig implementation](https://github.com/BenGalewsky/oasis).

## What does it do?

1. First, it downloads several hundred megabytes of data about business licenses, neighborhood and census tract boundaries, and socioeconomic indicators from the US Census Bureau's gazetteer files and the City of Chicago's data portal. This data is cached locally in a temp directory.
2. It determines each unique type of business license issued in Chicago, plus a range of years for which data about each type of license is available. This report is written to the `licenses.json` "index" file.
3. It produces a neighborhood-by-neighborhood abstract of socioeconomic data (poverty rates, educational attainment, etc.) and writes it to `socioeconomic.json`
4. It performs an analysis of how accessible each type of licensed business is to every census tract and neighborhood in Chicago. Neighborhood level data is written to the `community/` directory; census-level data is written to the `census/` directory. An individual data file is produced for every license type and every year for which data is available. For example, `retail-food-establishment-2014.json`
5. It identifies businesses that are the only business of their licensed kind within one mile of any census tract. A list of these "critical" businesses, plus the population of every census tract within one mile, are written to the `critical/` directory. An individual file is produced for every license type and every year for which data is available. For example, `critical-retail-food-establishment-2014.json`

Expect this program to consume about 1GB of memory and run for a couple hours (on decent hardware) to complete all analyses.

## How do I use it?

This program is written in Python 2.7. Assure that a compatible environment is active on your system, then:

1. Clone this repository:
```
$ git clone https://github.com/defano/chicago-oasis-data
```
2. Navigate to the project directory:
```
$ cd chicago-oasis-data
```
3. Execute the module (see table for options, none are required):
```
$ python -m oasis
```
4. Upon completion (takes about 2 hours), the program will produce three directories (each containing thousands of files) plus the license index file and the socioeconomic abstract:
```
census/
community/
critical/
licenses.json
socioeconomic.json
```

The program accepts the following command-line switches. When run without any options, all analyses are performed for all data.

Command-line Argument       | Description
----------------------------|-------------------------------
`-h`, `--help`              | Display help information and exit
`-lc <license-code>`        | Analyze only the given license code (e.g., `-lc 1472`); apply this option multiple times to analyze a set of license codes (e.g., `-lc 1472 -lc 1502 -lc 1002`). Has no effect on `licenses.json` or `socioeconomic.json` outputs.
`-o <path>`                 | Root directory path where output should be written (default is working directory, `./`)
`--analysis`                | Generate only accessibility and critical business analysis datasets; do not generate `licenses.json` or `socioeconomic.json`
`--index`                   | Generate only `licenses.json` index
`--socio`                   | Generate only `socioeconomic.json` data
`--clean`                   | Force download of all dependent datasets (even if a cached version already exists on disk)
`--start-at <license-code>` | Start analysis beginning at this license code (licenses are analyzed in ascending numerical order). Useful for restarting failed jobs.
`--community <dir-name>`    | Name of directory where neighborhood data should be written (default is `community`)
`--census <dir-name>`       | Name of directory where census data should be written (default is `census`)
`--critical <dir-name>`     | Name of directory where critical business data should be written (default is `critical`)

### Then what?

The datasets produced by this app are intended to be installed in the [Chicago Oasis](https://github.com/defano/chicago-oasis) web app. To do so,

1. Clone the Chicago Oasis app:
```
$ git clone https://github.com/defano/chicago-oasis
```
2. Copy the datasets into the project's `public/json` directory:
```
$ cp -r census community critical licenses.json socioeconomic.json /path/to/chicago-oasis/public/json
```
3. Fire up Chicago Oasis (see project page for details) and admire your handiwork:
```
$ npm start
```

## Analysis

This tool produces an analysis of business accessibility of each licensed category in every neighborhood and census tract for any year in which data is available. Accessibility is measured in terms of the number of businesses with one, two and three miles from the center of each census tract and as the sum total of `1 / distance` of each business to each census tract.

### Accessibility analysis files

Accessibility files are named according to the template `{license-description}-{year}.json` and placed in the `census/` and `community/` directories.

Each of these files are formatted as a JSON array containing a single object per each census tract or neighborhood. Census files contain 801 elements, each containing a property called `TRACT` providing the dotted-decimal census tract number for which the data applies (i.e., `8214.02`); neighborhood files contain 77 elements with a `COMMUNITY AREA` property providing the name of the corresponding neighborhood (like `EDISON PARK` or `ENGLEWOOD`). Each object contains desertification information about the corresponding area in a property called `ACCESS1` and `ACCESS2`. Additionally, within the census tract records we find properties containing the number of businesses that are located within one mile, two miles and three miles. These properties are called `ONE_MILE`, `TWO_MILE` and `THREE_MILE`, respectively.

For example, a census tract file would look like:

```
[
  {
    "BUSINESS_TYPE": "Accessory Garage",
    "THREE_MILE": 65,
    "ACCESS1": 115.73335508361284,
    "TRACT": "0814.01",
    "ACCESS2": 347.5703935471349,
    "YEAR": 2002,
    "ONE_MILE": 37,
    "TWO_MILE": 56
  },

  ...

]
```

Field              | Description
-------------------|--------------------------
`BUSINESS_TYPE`    | The license category of the businesses analyzed, for example `Music and Dance` or `Broker`
`ACCESS1`          | A floating point value equal to `1 / distance` of every business of this type to the centroid of analyzed area
`ACCESS2`          | A floating point value equal to `1 / distance ^ 2` of every business of this type to the centroid of the analyzed area
`YEAR`             | The four-digit calendar year for which the analysis was performed, for example `2017`
`COMMUNITY_AREA`   | The name of the community (neighborhood); only present in neighborhood files. For example, `LAKEVIEW`
`TRACT`            | A string dotted-decimal representation of the census tract; only present in census files.
`ONE_MILE`         | The number of businesses located within one mile of the center of the analyzed census tract
`TWO_MILE`         | The number of businesses located within two miles of the center of the analyzed census tract
`THREE_MILE`       | The number of businesses located within three miles of the center of the analyzed census tract

#### Critical Business Lists

A critical business is one whose demise would create a desert for a significant population (i.e., it's the only business of a given type within a mile of a certain population).

Critical business list files are named according to the template `critical-{license-description}-{year}.json` where `{license-description}` and `{year}` are defined the same as for accessibility indices. There is no need to partition this data on a per-census tract or per-neighborhood basis; the marker list is valid for the entire city.

Each of these files define a single array containing zero or more critical business objects consisting of the business name, location, address, and served population. For example:

```
[
  {
    "BUSINESS_TYPE": "Accessory Garage",
    "LEGAL_NAME": "LAKE STREET LOFTS, L.L.C.",
    "STATE": "IL",
    "DOING_BUSINESS_AS_NAME": "LAKE STREET LOFTS, L.L.C.",
    "POP_AT_RISK": 44462,
    "ZIP": 60607,
    "ADDRESS": "912 W LAKE ST",
    "YEAR": 2002,
    "LONGITUDE": -87.65039575,
    "LATTITUDE": 41.885725673
  },

  ...

]
```

Field                     | Description
--------------------------|--------------------------
`BUSINESS_TYPE`           | The business' license category description
`LEGAL_NAME`              | The legal name of the business
`DOING_BUSINESS_AS_NAME`  | The name under which the business operates
`POP_AT_RISK`             | The size of the population living within a one mile radius of the business
`ADDRESS`, `ZIP`, `STATE` | The legal address of the business. Note that this address may differ from the physical location where goods or services are offered.
`LONGITUDE`, `LATTITUDE`  | The geo-coded lat and long coordinates of the business address. Note the misspelling of the `LATTITUDE` field.

### Data sources

This tool makes use of the following source data sets.

Data Source                            | Description
---------------------------------------|---------------------------------------
Illinois Census Tracts ([download](https://www2.census.gov/geo/docs/maps-data/data/gazetteer/census_tracts_list_17.txt) / [view](https://www.census.gov/geo/maps-data/data/gazetteer2010.html)) | A list of every census tract in Illinois identified by a fully concatenated geographic code (State FIPS, County FIPS, census tract number).
Chicago Neighborhood Boundaries ([download](http://data.cityofchicago.org/api/views/igwz-8jzy/rows.csv?accessType=DOWNLOAD&api_foundry=true) / [view](https://data.cityofchicago.org/Facilities-Geographic-Boundaries/Boundaries-Neighborhoods/bbvz-uum9/data)) | A table of neighborhood polygons (geographic outlines), community area numbers and neighborhood names.
Neighborhood to Census Tract Equivalency ([view](http://robparal.blogspot.com/2012/04/census-tracts-in-chicago-community.html)) | A manually-generated mapping of neighborhood to census tracts from "Chicago Data Guy" Rob Paral. Downloaded and committed into this repository since no API exists for downloading Rob's file directly.
Neighborhood Socioeconomic Indicators ([download](http://data.cityofchicago.org/api/views/kn9c-c2s2/rows.csv?accessType=DOWNLOAD&api_foundry=true) / [view](https://data.cityofchicago.org/Health-Human-Services/Census-Data-Selected-socioeconomic-indicators-in-C/kn9c-c2s2/data)) | A 2008 table of socioeconomic indicators for each of Chicago's 77 officially recognized communities.
Chicago Business licenses ([download](http://data.cityofchicago.org/api/views/r5kz-chrr/rows.csv?accessType=DOWNLOAD&api_foundry=true) / [view](https://data.cityofchicago.org/Community-Economic-Development/Business-Licenses/r5kz-chrr/data)) | Approximately a million business license records stretching over 20 years.

## Questions that nobody has ever asked

#### It crashed. What now?
It probably crashed because a) you ran out of memory (i.e., `Killed: 9`), or b) a dataset changed in an unexpected way such as a required row was deleted or a new record was added with missing or bogus data.

If you've discovered that a change in source data is breaking the analysis, please report an issue.

#### Why is there data available for future years?
Because some businesses have licenses valid into the future. This tool provides the same analysis of these forward-looking business licenses as it does for historical and present licenses. That said, be aware that this subset does not accurately reflect all the businesses likely to be active during these years.

#### Why do I sometimes see two or more critical businesses near one another? This would seem to violate the concept, wouldn't it?
It may seem to violate the concept, but in fact it does not. Imagine two businesses separated by a block, east and west of one another. Since we define a critical business to be one that serves a large population within one mile of its location, it’s possible that closing the east business would put the corresponding eastern population at a distance of more than a mile from the western business--even if by only one block.

#### Why does the street view sometimes show an address/area that doesn't appear to have anything to do with the business in question?
The critical business markers are based on the latitude and longitude associated with the license. In some cases the business license may be addressed to an owner’s residence or a holding company, even if the product or service is being offered elsewhere. Think of food trucks, peddlers, and similarly mobile businesses...
