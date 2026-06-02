Steward Basin
Steward Basin is an independent environmental and public records mapping project focused on the Uintah Basin region of Utah, including:
•	Duchesne County
•	Uintah County
•	Uintah & Ouray Reservation
•	Ute Tribal lands
•	Regional oil & gas infrastructure
•	Air quality and environmental health impacts
The project combines:
•	GIS mapping
•	automated web scraping
•	public meeting archives
•	zoning and permitting records
•	environmental complaints
•	public health indicators
•	industrial infrastructure data
•	historical county documents
•	community-reported impacts
into a searchable and mapable public intelligence platform.
________________________________________
Project Goals
Steward Basin exists to:
•	document environmental impacts
•	preserve public records
•	improve transparency
•	track industrial development
•	visualize health and environmental trends
•	identify historical patterns in permitting and enforcement
•	support community research and investigative journalism
•	create accessible public-facing environmental data tools
________________________________________
Current Features
Interactive Mapping
•	Oil & gas infrastructure layers
•	Air quality datasets
•	Complaint tracking
•	Wells and industrial sites
•	GeoJSON overlays
•	Historical map support
Automated Scraping
Python + Playwright scrapers collect:
•	county planning documents
•	commission minutes
•	zoning records
•	CUP approvals
•	GIS resources
•	environmental references
•	health-related public documents
•	tribal and reservation-related records
Keyword Detection
Current keyword systems scan for:
•	flaring
•	odor
•	pollution
•	contamination
•	dust
•	H2S
•	benzene
•	public complaints
•	domestic violence
•	MMIW
•	tribal issues
•	trafficking
•	industrial housing
•	cancer
•	COPD
•	respiratory illness
•	environmental exposure
________________________________________
Tech Stack
Frontend:
•	HTML
•	CSS
•	JavaScript
•	Leaflet.js
Backend / Data:
•	Python
•	Playwright
•	BeautifulSoup
•	GeoJSON
Potential Future Stack:
•	PostgreSQL/PostGIS
•	FastAPI
•	Node.js APIs
•	Automated ETL pipelines
•	Cloud hosting
•	Scheduled scrapers
•	AI-assisted document classification
________________________________________
Folder Structure
/archive
/scripts
/geoJson
/data
/maps
/output
________________________________________

Data Workflow
Steward Basin follows a three-stage data preservation process.
Stage 1: Raw Data
Stored in:
archive/raw/
Examples:
•	ZIP archives
•	PDF reports
•	Original downloads
•	Government exports
Raw files are never modified.
Stage 2: Processed Data
Stored in:
archive/data/
Examples:
•	Cleaned JSON files
•	Classified incidents
•	Complaint datasets
•	Environmental monitoring datasets
Processed data is generated from raw sources.
Stage 3: Website Data
Used directly by the map application.
Examples:
•	complaints.json
•	ozone.json
•	pm25.json
•	pm10.json
These files are optimized for public visualization.
________________________________________
Long-Term Vision
Steward Basin is designed to become a continuously updating regional monitoring platform capable of:
•	automated data ingestion
•	historical trend analysis
•	permit tracking
•	environmental risk visualization
•	public alerts
•	archival preservation
•	investigative research support
Future plans include:
•	automated daily scraping
•	real-time update alerts
•	searchable document indexing
•	PDF OCR processing
•	AI tagging and categorization
•	time-series environmental maps
•	public dashboard interfaces
•	API access
________________________________________
Data Sources
Potential data sources include:
•	Duchesne County
•	Uintah County
•	Uintah & Ouray Ute Tribe
•	Utah state agencies
•	EPA datasets
•	Utah Division of Oil, Gas & Mining
•	Utah Department of Health
•	TriCounty Health
•	UBMC / Ashley Regional
•	GIS portals
•	planning commission archives
•	public hearing records
________________________________________
Ethics & Transparency
This project is intended for:
•	public interest research
•	environmental transparency
•	historical preservation
•	data accessibility
Steward Basin does not claim causation without evidence and aims to preserve source links and original records whenever possible.
________________________________________
Future Monetization Possibilities
Potential future directions include:
•	licensing datasets
•	journalism partnerships
•	environmental consulting
•	public records intelligence services
•	nonprofit grant funding
•	subscription dashboards
•	university research collaboration
•	investigative reporting tools
•	API access for developers
•	public environmental monitoring products
________________________________________
Data Sources & Credits
Steward Basin relies upon publicly available information from numerous organizations and agencies. Data ownership remains with the original source agencies.
Major sources currently include:
Environmental Incident Data
•	Utah Department of Environmental Quality (DEQ)
o	Environmental Incident Database
o	Legacy Environmental Incident Search Portal
o	Environmental Incident Reporting System
Air Quality Data
•	Utah Division of Air Quality (DAQ)
•	Uinta Basin Ozone Studies
•	Utah State University (USU)
•	Bingham Research Center
•	TriCounty Health Department
GIS Data
•	Utah Automated Geographic Reference Center (AGRC)
•	Utah GIS Portal
•	Duchesne County GIS
•	Uintah County GIS
•	Bureau of Land Management (BLM)
•	SITLA
Oil & Gas Data
•	Utah Division of Oil, Gas and Mining (DOGM/OGM)
•	Utah Oil & Gas GIS Resources
•	Well Permit and Production Records
Research & Academic Sources
•	Utah State University
•	University of Utah
•	Utah Center for High Performance Computing (CHPC)
•	NOAA
•	EPA
Local Government Sources
•	Duchesne County
•	Uintah County
•	Planning Commission Records
•	County Commission Records
•	Public Hearing Archives
Steward Basin attempts to preserve attribution and source links whenever possible.
________________________________________

Status
Active development.
Initial archive build focuses on records from approximately 2017-present, with future plans for historical expansion.
Current Limitations
- Not all environmental complaints are publicly available.
- Some records require manual review.
- Historical records may exist in multiple databases.
- Duplicate records may still exist.
- Location data occasionally requires manual verification.
- Steward Basin preserves source records whenever possible.
- Correlation does not imply causation, but, this is being built to be used for research and further studies that could be conducted based off of the data provided on this website.

