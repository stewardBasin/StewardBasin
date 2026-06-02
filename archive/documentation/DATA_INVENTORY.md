# Steward Basin Data Inventory

## Website Files

## Active Website Data

These files are currently loaded by stewardBasin.js.

geoJson/facilities.geojson
Used for the facilities layer.

archive/data/complaints.json
Used for complaint markers and the complaint chart.

archive/data/deq_incidents_2016_present.json
Used for the current DEQ incident marker layer and DEQ incident chart.

archive/data/deq_incidents_pre2016.json
Used for the historical DEQ incident marker layer and DEQ incident chart.

archive/data/airQuality.json
Used for ozone, PM2.5, and PM10 charts.

archive/data/h2s.json
Used for H2S report markers.

archive/data/wells.json
Used for well markers.

archive/data/monitoring_sites.json
Used for monitoring station markers and the live AQ carousel.

archive/data/live_air_quality.json
Used for the live AQ card and station carousel.

archive/data/chpc_live_air_quality.json
Used for CHPC ozone/PM readings and regional ozone status.

Active website files:

 index.html
 style.css
 stewardBasin.js

Purpose:
Main public website interface.

---

## GeoJSON Layers

Location:

geoJson/

Purpose:
Map layers and geographic datasets.

Status:
Active

---

## Air Quality Data

Location:

archive/data/

Files:

 airQuality.json
 chpc_live_air_quality.json
 chpc_fixed_site_map_data.json
 chpc_mobile_map_data.json
 monitoring_sites.json

Purpose:
Air quality monitoring and mapping.

Status:
Active

---

## Complaint Data

Location:

archive/data/

Files:

 complaints.json
 dust_complaints.json
 h2s_odor_complaints.json
 noise_flaring_complaints.json

Purpose:
Citizen complaints and public testimony.

Status:
Active

---

## DEQ Incident Data

deq_incidents.json

Purpose:
Original map-ready environmental incident dataset derived from
Utah DEQ Open Data environmental incident records.

Contains:
-Incident metadata
-Coordinates
-Company names
-County
-Incident descriptions
-Full raw DEQ record

Status:
Legacy master incident dataset.

Used as source for later incident classification and filtering workflows.

Location:

archive/data/

Files:

 deq_incidents_pre2016.json
 deq_incidents_2016_present.json
 deq_incidents.json
 deq_incidents_classified.json
 deq_duchesne_2020_2024.json

Purpose:
Utah DEQ environmental incident records.

Status:
Active

---

## Raw Archives

Location:

archive/raw/

Purpose:
Original downloads preserved exactly as obtained.

Status:
Archive only
Do not modify.

# DATA INVENTORY

Last Updated: June 2026

Purpose:
Master inventory of datasets currently used by Steward Basin.

## Active Website Data

archive/data/complaints.json
Purpose:
Citizen complaints and public testimony.

archive/data/airQuality.json
Purpose:
Historical air quality data.

archive/data/live_air_quality.json
Purpose:
Current air quality readings.

archive/data/chpc_live_air_quality.json
Purpose:
Current CHPC air quality feeds.

archive/data/monitoring_sites.json
Purpose:
DAQ and CHPC monitoring station locations.

archive/data/wells.json
Purpose:
Oil and gas well locations.

archive/data/h2s.json
Purpose:
H2S-related complaints and findings.

archive/data/deq_incidents_2016_present.json
Purpose:
Environmental incidents from 2016-present.

archive/data/deq_incidents_pre2016.json
Purpose:
Historical environmental incidents.

archive/data/deq_duchesne_2020_2024.json
Purpose:
Duchesne County DEQ incidents extracted from legacy portal.

archive/data/deq_environmental_incidents_all.json
Purpose:
Master DEQ incident archive.

archive/data/deq_environmental_incidents_basin.json
Purpose:
Uintah Basin subset.

archive/data/entities.json
Purpose:
Tracked entities list.

archive/data/entity_summary.json
Purpose:
Entity mention statistics.

archive/data/industrial_operations_candidates.json
Purpose:
Potential industrial projects extracted from minutes.

archive/data/dust_complaints.json
Purpose:
Dust-related complaints.

archive/data/noise_flaring_complaints.json
Purpose:
Noise and flaring complaints.