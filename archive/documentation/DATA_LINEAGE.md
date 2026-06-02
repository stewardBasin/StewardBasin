# Steward Basin Data Lineage

## Purpose

This document tracks the origin, transformations, and dependencies of datasets used in the Steward Basin project.

---

# SOURCE DOCUMENTS

## Duchesne County Planning Commission Minutes

Location:
data/raw/planning_commission/

Purpose:
Original source documents downloaded from Duchesne County.

Used By:

* entity extraction
* complaint extraction
* industrial project extraction
* political tracking

Outputs:

* entities.json
* entity_summary.json
* complaint_findings.json
* industrial_operations_candidates.json

---

## Utah DEQ Incident Records

Location:
data/raw/deq/

Purpose:
Original Utah DEQ environmental incident records.

Outputs:

* deq_incidents.json
* deq_environmental_incidents_all.json
* deq_environmental_incidents_basin.json

---

# DERIVED DATASETS

## deq_incidents.json

Source:
Utah DEQ Incident Records

Purpose:
Map-ready environmental incidents dataset.

Outputs:

* website incident layers
* incident classification workflows

Status:
Master dataset

---

## entities.json

Source:
Planning Commission Minutes

Purpose:
List of tracked entities and entity categories.

Example:

Ovintiv → Oil Company
Ron Winterton → Political
Nine Mile LLC → Developer

Outputs:

* entity matching
* entity reporting

---

## entity_summary.json

Source:
entities.json + extracted meeting references

Purpose:
Counts occurrences by:

* year
* county
* entity type

Example:

Ovintiv:
2023 = 11
2024 = 4

Ron Winterton:
91 total mentions

Outputs:

* dashboard statistics
* website reports

---

# KNOWN DATA ISSUES

## Duplicate Entities

Potential merges:

Jake Woodland
Jacob Woodland

Crescent Point
Crescent Point Energy

Mike Stegnal
Michael Stegnal

Status:
Needs entity normalization process.

---

# PIPELINES

Planning Commission Minutes
↓
OCR / Text Extraction
↓
Entity Extraction
↓
entities.json
↓
entity_summary.json

DEQ Records
↓
deq_incidents.json
↓
deq_environmental_incidents_all.json
↓
deq_environmental_incidents_basin.json
↓
Website Incident Layer
