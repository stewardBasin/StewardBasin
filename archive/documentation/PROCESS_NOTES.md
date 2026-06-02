# Steward Basin Environmental Data Collection Workflow

## Project Goal

Create a public environmental transparency website for the Uintah Basin that allows residents to:

View environmental complaints
View air quality data
View oil and gas incidents
View DEQ environmental incidents
View monitoring station data
View historical records
Access original source documents and PDFs

The project is designed so that every map point can be traced back to an original public source.

---

# PHASE 1: INITIAL WEBSITE BUILD

## Original Website Structure

The website began as a simple HTML page using:

HTML
CSS
JavaScript
Bootstrap
Leaflet

Files:

```text
index.html
style.css
stewardBasin.js
```

### Goal

Display environmental complaints on an interactive map.

### Initial Problems

#### Problem: Markers hardcoded in JavaScript

Originally all complaints were stored directly inside:

```javascript
stewardBasin.js;
```

This made the file difficult to maintain.

#### Resolution

Moved complaint records into:

```text
complaints.json
```

Benefits:

Easier editing
Easier expansion
Cleaner code
Better separation of data from logic

---

# PHASE 2: JSON DATA STRUCTURE

## Why JSON Was Introduced

JSON (JavaScript Object Notation) is a structured data format.

Example:

```json
{
  "date": "2024-05-01",
  "type": "Noise Complaint",
  "lat": 40.1633,
  "lng": -110.4029
}
```

Benefits:

Understandable code for any future developers or handlers.
Machine readable, hopefully. Trying to make it so:
-Can be imported into databases, GIS systems,
web applications, and analysis tools.
-Easy to load into JavaScript.

Can later become databases and expanded upon.

Ethically bound by by responsible coding.

Files created:

### Complaint Datasets

```text
complaints.json
verified_complaints.json
h2s.json
h2s_odor_complaints.json
```

Purpose:

Environmental complaints
Public testimony
Odor complaints
H2S complaints
Noise complaints
Dust complaints
Truck traffic complaints
Citizen reports

---

### Air Quality Datasets

```text
airQuality.json
ozone.json
pm25.json
pm10.json
monitoring_sites.json
```

Purpose:

Ozone tracking
PM2.5 monitoring
PM10 monitoring
Air quality visualizations
Monitoring station mapping

---

### DEQ Incident Datasets

deq_environmental_incidents_basin.json
deq_incidents.json
deq_incidents_classified.json
deq_incidents_2016_present.json
deq_incidents_pre2016.json
deq_duchesne_2020_2024.json

Purpose:

Environmental incident tracking
Spill reports
Produced water releases
Crude oil spills
Fuel spills
H2S releases
Wastewater releases
Historical incident analysis

---

### Archive Review Datasets

```text
all_2016_present.json
historical_archive_pre2016.json

2016_present_dust_pm10.json
2016_present_h2s_odor.json
2016_present_flaring_noise.json
2016_present_oil_gas_operations.json
2016_present_policy_air_quality.json
2016_present_health_impacts.json

industrial_operations_candidates.json
```

Purpose:

Large-scale document review and categorization.

These files were generated from county records,
meeting minutes, public documents, planning
records, and historical archives.

---

### Source Tracking Datasets

```text
source_archive_index.json
deq_duchesne_2024_2026_pdf_links.txt
```

Purpose:

Preserve source provenance
Track downloaded reports
Document collection workflows
Support transparency and reproducibility

---

### Planned Datasets

```text
radon.json
harmful_algal_blooms.json
wildfire_smoke.json
deq_master_incidents.json
cancer_registry_research.json
```

Purpose:

Future environmental and public health layers.

---

# PHASE 3: COUNTY MEETING COMPLAINT COLLECTION

## Sources Reviewed

### Duchesne County

County Commission meetings
Planning Commission meetings
Public hearings
Land Use hearings

### Uintah County

County Commission meetings
Planning Commission meetings
Land Use Authority meetings

### Data Captured

Examples:

Noise complaints
Vibration complaints
Dust complaints
Truck traffic complaints
Flaring complaints
Air quality complaints

---

# PHASE 4: AIR QUALITY DATA

## Goal

Add air quality layers.

Categories:

Ozone
PM2.5
PM10
Monitoring stations
Smoke

Files:

```text
ozone.json
pm25.json
pm10.json
monitoring_sites.json
```

Planned future additions:

H2S
Radon
Harmful Algal Blooms/Cyanobacteria outbreaks

---

# PHASE 5: DEQ INCIDENT DATABASE DISCOVERY

## Database #1

Legacy DEQ Environmental Incident Database

Website:

https://eqspillsps.deq.utah.gov/Search_Public.aspx

### Discovery

Searches appeared incomplete.

At first it looked like records stopped around 2020.

### Investigation

Created Python scripts to analyze downloaded records.

Scripts:

```text
fetch_deq_environmental_incidents.py
filter_deq_pre2016.py
filter_deq_2016_present.py
count_deq_incidents_by_year.py
```

### Findings

Records found:

````text

2000-2020 - turned up some records from before 1990, sorted.

### Mistake

Initially assumed database was complete through present day and then realized that there was a new website being used as of 2024 which is why the records were just dropping off aside of gathered complaints from public documents and county records.

### Resolution

Determined database appears to stop updating around 2020.

---

# PHASE 6: LEGACY DEQ PORTAL EXTRACTION

## Challenge

Searches capped at:

```text
500 records
````

This initially made collection appear impossible.

### Discovery

Date filters can be used.

Example:

```text
1/1/2020 >
```

instead of searching all records.

### Result

Able to retrieve:

```text
2020 through May 2024
```

for:

- Duchesne County
- Uintah County

### Download Method

Manual batch downloads.

Site limitation:

```text
100 selected reports maximum
```

Reports downloaded in groups.

Saved as ZIP archives.

Folder:

```text
archive/raw/deq_portal_downloads/
```

---

# PHASE 7: MAP COORDINATE RESEARCH

## Challenge

DEQ reports often store coordinates as:

```text
UTM Easting
UTM Northing
```

instead of latitude/longitude.

Example:

```text
UTMe = 571684
UTMn = 4471874
```

### Investigation

Opened:

MapSearchDirect.aspx

and inspected source code.

### Discovery

Map links contain UTM coordinates.

Future scripts can convert:

```text
UTM → Latitude/Longitude
```

for Steward Basin map layers.

---

# PHASE 8: NEW DEQ INCIDENT PORTAL

## Database #2

New DEQ Incident Reporting System

Website:

https://deqspillsps.deq.utah.gov

### Discovery

Contains records through:

```text
2026
```

and continues receiving updates.

### Search Example

County:

```text
DUCHESNE
```

Date range:

```text
2024-present
```

Result:

```text
56 incidents
```

found.

### Important Finding

This portal contains records missing from the legacy database.

---

# PHASE 9: PDF EXTRACTION ATTEMPTS

## Attempt #1

Direct Python downloads.

Result:

HTML pages downloaded instead of PDFs.

### Cause

Site uses authentication/session handling.

### Resolution

Extracted record IDs from browser source.

Example:

```text
500eq000013JY07AAF
```

Generated:

```text
deq_duchesne_2024_2026_pdf_links.txt
```

containing record identifiers.

---

# PHASE 10: BULK PDF COLLECTION

Folder:

archive/raw/deq_portal_downloads/duchesne_2024_2026_pdfs/

Contains:

Individual incident PDFs
Original reports
Raw source documents

Important rule:

NEVER modify these files.

They are evidence/source documents.

---

# PHASE 11: DATA PRESERVATION STRATEGY

The project now follows:

## RAW DATA

Never modified.

Stored in:

archive/raw/

Examples:

zip files
pdf files
downloads
original exports

---

## PROCESSED DATA

Generated from raw files.

Stored in:

archive/data/

These files are created by Python scripts,
manual review, classification, deduplication,
or data cleaning workflows.

Examples:

deq_incidents.json
deq_incidents_classified.json
deq_incidents_2016_present.json
deq_incidents_pre2016.json

### Incident Data

deq_incidents.json
Raw DEQ incident records collected from public databases.

deq_incidents_classified.json
Same incidents categorized into: - Produced Water - Oil Spill - H2S Release - Fuel Spill - Wastewater Release - etc.

deq_incidents_2016_present.json
Records filtered for modern analysis.

deq_incidents_pre2016.json
Historical records preserved separately.

deq_duchesne_2020_2024.json
deq_duchesne_2024_2026_pdf_links.txt

source_archive_index.json

all_2016_present.json
historical_archive_pre2016.json

Purpose:
Generated during automated review of county,
planning, and environmental records to isolate
potential H2S and odor-related concerns from dust,
noise, and ozone pollution.

Dates: May-June 2/2026

2016_present_dust_pm10.json
2016_present_h2s_odor.json
2016_present_flaring_noise.json
2016_present_oil_gas_operations.json
2016_present_policy_air_quality.json
2016_present_health_impacts.json

industrial_operations_candidates.json
verified_complaints.json
deq_environmental_incidents_basin.json
airQuality.json
monitoring_sites.json
h2s.json
h2s_odor_complaints.json
ozone.json
pm25.json
pm10.json
radon.json (to be done)
source_archive_index.json

Date: June/2/2026-future additions

---

## WEBSITE DATA

Simplified datasets used by map.

Examples:

complaints.json
h2s.json
ozone.json
pm25.json
pm10.json
clean_data/sorted.json

---

# LESSONS LEARNED

1. Government databases often have unforeseen limits.

2. Search interfaces are not always complete and require a lot of manually fact-checking and human guidance and sorting through of the data looking to be collected.

3. Always preserve original files- and document EVERYTHING.

4. Never overwrite raw data or use a python crawler unethically.

5. Verify assumptions with scripts and data.

6. Record collection methods immediately because as I did more and more crawls, it got hard to keep track of everything in an organized way. So I stopped and spent a day sorting and organizing all my files, folders, and triple checking that all my JS was referencing proper file names and destinations.

7. Document every workflow, diligently.

8. Small repeatable scripts are better than large complicated scripts.

9. Public records are often fragmented across multiple systems, python is great for helping sort through duplicates and unimportant data. I love pythons extraction capabilities.

10. Every map point should be traceable to an original source document, which am still figuring out how to make those archives publically available on the website, but I have to find out if that is legal or I need permissions.

---

# NEXT STEPS

## DEQ

Download remaining 2024-present PDFs
Extract metadata
Convert UTM coordinates
Build incident layer

## Air Quality

Expand AQ monitoring network
Add PM10 layer
Add radon layer

## Environmental Complaints

Continue search for complaint archives
earch county records
Search state records
Search public comment records

## Transparency

Create website page:

To be Completed, currently still just in VSC and computer folders.

containing:

PDFs
Reports
Datasets
Meeting minutes
Monitoring station data
Original downloads

Every dataset should link back to source material.
May 2026

Started Steward Basin.

Initial map created using:
-HTML
-CSS
-Leaflet

Early issues:
-Node not installed
-npx errors
-CORS errors
-duplicate map variable declarations
-JSON formatting errors

Resolved by:
-installing Node
-moving data into external JSON files
-correcting JavaScript structure

Added:
-complaint layers
-air quality layers
-DEQ incident layers
-monitoring station layers

June 2026

Discovered DEQ legacy incident portal.

Downloaded:
2020-2024 Duchesne archive

Created:
deq_duchesne_2020_2024.json

Discovered:
new Salesforce-based DEQ incident portal

Downloaded:
2024-2026 incident records

Created:
deq_duchesne_2024_2026_pdf_links.txt

Started PDF archive preservation workflow.