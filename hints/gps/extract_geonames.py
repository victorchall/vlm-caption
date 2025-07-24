import csv

# download from https://download.geonames.org/export/dump/ and unzip
INPUT_FILE = "allCountries.txt" # core data
COUNTRY_CODE_LUT_FILE = "countryInfo.txt"
ADMIN1CODES_LUT_FILE = "admin1CodesASCII.txt"

OUTPUT_FILE = "extracted_location_data.tsv"

country_lookup = {}

with open(COUNTRY_CODE_LUT_FILE, 'r', newline='', encoding='utf-8') as f:
    reader = csv.reader(f, delimiter='\t', )
    
    for row in reader:
        if not row[0].startswith("#"):
            key = row[0].strip() # ISO-3166 (matches data), iso3, iso-numeric, fips, country_name
            value = row[4].strip() # ascii name of admin1
            
            country_lookup[key] = value

admin1code_lookup = {}

with open(ADMIN1CODES_LUT_FILE, 'r', newline='', encoding='utf-8') as f:
    reader = csv.reader(f, delimiter='\t')
    
    for row in reader:
        if len(row) >= 2:
            key = row[0].strip() # COUNTRY_CODE.ADMIN1CODE ex US.NY or VN.53
            value = row[1].strip() # ascii name of admin1
            
            admin1code_lookup[key] = value

            # sanity check, see if we find Indiana, United States (US.IN) while parsing
            # if key == "US.IN":
            #     print("found US.IN")

# Define the columns needed
LOC_NAME_COL_IDX = 1
LATITUDE_COL_IDX = 4
LONGITUDE_COL_IDX = 5
COUNTRYCODE_COL_IDX = 8
ADMIN1CODE_COL_IDX = 10
TIMEZONE_COL_IDX = 17
# define which are in the output (admin1zone name will also be appended)
COLUMNS_TO_EXTRACT = [LATITUDE_COL_IDX, LONGITUDE_COL_IDX, LOC_NAME_COL_IDX]

def exclude_filter(columns):
    # locations marked (historical) no longer exist so skipped
    if "historical" in columns[LOC_NAME_COL_IDX]:
        return True
    # TODO other filters if needed

    return False

hit = 0
miss = 0
with open(INPUT_FILE, "r", newline="", encoding="utf-8") as infile, \
     open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as outfile:

    for line_number, line in enumerate(infile):
        columns = line.strip().split("\t")

        if exclude_filter(columns):
            continue

        extracted = [columns[i] for i in COLUMNS_TO_EXTRACT]

        admin1name = ""
        country_dot_admin1_key = ""
        country_name = ""

        if columns[COUNTRYCODE_COL_IDX]:
            try:
                country_name = country_lookup[columns[COUNTRYCODE_COL_IDX]]
            except KeyError as ex:
                print(f"can't find country for {columns[COUNTRYCODE_COL_IDX]}, {columns}")

        # don't attempt to lookup the admin1 name if the code is invalid or n/a, see https://download.geonames.org/export/dump/readme.txt
        if not columns[ADMIN1CODE_COL_IDX] == "00" \
            and not columns[ADMIN1CODE_COL_IDX] == "" \
            and not columns[COUNTRYCODE_COL_IDX] == "":
            try:
                country_dot_admin1_key = f"{columns[COUNTRYCODE_COL_IDX]}.{columns[ADMIN1CODE_COL_IDX]}"
                admin1name = admin1code_lookup[country_dot_admin1_key]
                hit += 1
            except KeyError as ex:
                # unfortunately there are a lot of misses, typically no matching admin1code for the given country
                miss +=1
                print(f"Can't find admin1name for {country_dot_admin1_key}: {columns}")
        else:
            # unfortunately there are a lot of missing or n/a admin1codes
            miss +=1
            print(f"No valid Admin1code {country_dot_admin1_key}: {columns}")

        #extracted.append(country_dot_admin1_key) # for debugging
        extracted.append(admin1name)
        extracted.append(country_name)

        outfile.write("\t".join(extracted) + "\n")

# approx 13m and 281k
print(f"hit: {hit}, miss:{miss}")