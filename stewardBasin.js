// =======================
// MAP SETUP
// =======================

const map = L.map("map").setView([40.1633, -110.4029], 9);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

// =======================
// PARCEL LAYER
// =======================

const parcels = L.esri
  .dynamicMapLayer({
    url: "https://gis.duchesnecountygis.org/server/rest/services/PUBLIC/Tax_Parcel_Public/MapServer",
    opacity: 0.15,
  })
  .addTo(map);

// =======================
// STATE
// =======================

let complaintsVisible = true;
let facilitiesVisible = true;
let wellsVisible = true;
let h2sVisible = true;
let parcelsVisible = true;
let monitoringVisible = true;
let deqIncidentsVisible = true;
let historicalDEQVisible = false;

const complaintMarkers = [];
const wellMarkers = [];
const h2sMarkers = [];
const monitoringMarkers = [];
const deqIncidentMarkers = [];
const historicalDEQMarkers = [];

let facilitiesGeoJsonLayer;

// =======================
// HELPERS
// =======================

function pollutantBadge(status) {
  if (status === "LOW") return "🟢 LOW";
  if (status === "MODERATE") return "🟡 MODERATE";
  if (status === "HIGH") return "🟠 HIGH";
  if (status === "VERY HIGH") return "🔴 VERY HIGH";
  return "⚪ No Local Monitor";
}

function ozoneLevel(value) {
  const v = Number(value);
  if (isNaN(v)) return "No Local Monitor";
  if (v >= 71) return "VERY HIGH";
  if (v >= 56) return "HIGH";
  if (v >= 46) return "MODERATE";
  return "LOW";
}

function pm25Level(value) {
  const v = Number(value);

  if (isNaN(v)) return "No Local Monitor";
  if (v >= 35) return "VERY HIGH";
  if (v >= 12) return "HIGH";
  if (v >= 8) return "MODERATE";

  return "LOW";
}

function pm10Level(value) {
  const v = Number(value);
  if (isNaN(v)) return "No Local Monitor";
  if (v >= 150) return "VERY HIGH";
  if (v >= 50) return "HIGH";
  if (v >= 25) return "MODERATE";
  return "LOW";
}
function getValue(value, fallback = "Unknown") {
  return value || fallback;
}

function safeFetchJson(path, label) {
  return fetch(path).then((response) => {
    if (!response.ok) {
      throw new Error(`${label} not found: ${path}`);
    }
    return response.json();
  });
}

function cleanReading(value, fallback = "No current reading") {
  if (value === null || value === undefined || value === "--" || value === "") {
    return fallback;
  }
  return value;
}

function getMilesBetween(lat1, lng1, lat2, lng2) {
  const R = 3958.8;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLng = ((lng2 - lng1) * Math.PI) / 180;

  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLng / 2) ** 2;

  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function findNearestChpcWithOzone(site, chpcStations) {
  if (!site || !chpcStations || !Array.isArray(chpcStations)) return null;

  const siteLat = Number(site.lat);
  const siteLng = Number(site.lng);

  if (isNaN(siteLat) || isNaN(siteLng)) return null;

  const candidates = chpcStations
    .filter((station) => station.ozone?.value && station.lat && station.lng)
    .map((station) => ({
      ...station,
      distanceMiles: getMilesBetween(
        siteLat,
        siteLng,
        Number(station.lat),
        Number(station.lng),
      ),
    }))
    .sort((a, b) => a.distanceMiles - b.distanceMiles);

  return candidates[0] || null;
}

function normalizeName(name) {
  return String(name || "")
    .toLowerCase()
    .replace("#4", "")
    .replace("aq monitor", "")
    .replace("area monitor", "")
    .replace("monitor", "")
    .replace("research", "")
    .replace("site", "")
    .replace("/", " ")
    .trim();
}

function getAQIColor(aqi) {
  const value = Number(aqi);

  if (isNaN(value)) return "#7f9272";
  if (value <= 50) return "#2ecc71";
  if (value <= 100) return "#f1c40f";
  if (value <= 150) return "#e67e22";
  if (value <= 200) return "#e74c3c";
  return "#8e44ad";
}

function getAQIStatus(aqi) {
  const value = Number(aqi);

  if (isNaN(value)) return "No current reading";
  if (value <= 50) return "Good";
  if (value <= 100) return "Moderate";
  if (value <= 150) return "Unhealthy for Sensitive Groups";
  if (value <= 200) return "Unhealthy";
  return "Very Unhealthy";
}

function formatMeasurements(measurements) {
  if (Array.isArray(measurements)) {
    return measurements.join(", ");
  }

  if (
    measurements === null ||
    measurements === undefined ||
    measurements === ""
  ) {
    return "Unknown";
  }

  return measurements;
}

function getPM25Status(value) {
  const pm25 = Number(value);

  if (isNaN(pm25)) return "Monitoring gap";
  if (pm25 >= 35.5) return "Unhealthy for Sensitive Groups";
  if (pm25 >= 9.1) return "Moderate / Elevated";
  return "Good";
}

function getOzoneStatusPPBV(value) {
  const ozone = Number(value);

  if (isNaN(ozone)) return "Monitoring gap";
  if (ozone >= 71) return "Unhealthy for Sensitive Groups";
  if (ozone >= 55) return "Moderate / Elevated";
  if (ozone >= 45) return "Watch";
  return "Good";
}

function getPollutantColorFromStatus(status) {
  if (status.includes("Unhealthy")) return "#e67e22";
  if (status.includes("Moderate") || status.includes("Elevated"))
    return "#f1c40f";
  if (status.includes("Watch")) return "#f1c40f";
  if (status === "Good") return "#2ecc71";
  return "#7f9272"; // monitoring gap / no data
}
function getWorstStationColor(station, chpcStation) {
  const statuses = [];

  if (station && station.aqi !== "--") {
    statuses.push(getAQIStatus(station.aqi));
  }

  if (chpcStation && chpcStation.ozone && chpcStation.ozone.value) {
    statuses.push(getOzoneStatusPPBV(chpcStation.ozone.value));
  }

  if (chpcStation && chpcStation.pm25 && chpcStation.pm25.value) {
    statuses.push(getPM25Status(chpcStation.pm25.value));
  }

  if (statuses.some((s) => s.includes("Unhealthy"))) return "#e67e22";
  if (statuses.some((s) => s.includes("Moderate") || s.includes("Elevated")))
    return "#f1c40f";
  if (statuses.some((s) => s.includes("Watch"))) return "#f1c40f";
  if (statuses.some((s) => s === "Good")) return "#2ecc71";

  return "#7f9272";
}

function formatPM10AQI(value) {
  if (value === null || value === undefined || value === "--" || value === "") {
    return "No PM10 reading";
  }

  return `AirNow AQI ${value}`;
}

function formatAirNowOzone(value) {
  if (value === null || value === undefined || value === "--" || value === "") {
    return "No AirNow ozone AQI";
  }

  return `AirNow AQI ${value}`;
}

function formatAirNowPM25(value) {
  if (value === null || value === undefined || value === "--" || value === "") {
    return "No AirNow PM2.5 AQI";
  }

  return `AirNow AQI ${value}`;
}

function formatChpcOzone(chpcStation) {
  if (!chpcStation || !chpcStation.ozone || !chpcStation.ozone.value) {
    return "No CHPC ozone reading";
  }

  return `${chpcStation.ozone.value} ${chpcStation.ozone.unit || "ppbv"}`;
}

function formatChpcPM25(chpcStation) {
  if (!chpcStation || !chpcStation.pm25 || !chpcStation.pm25.value) {
    return "No CHPC PM2.5 reading";
  }

  return `${chpcStation.pm25.value} ${chpcStation.pm25.unit || "µg/m³"}`;
}

function formatChpcPM10(chpcStation) {
  if (!chpcStation || !chpcStation.pm10 || !chpcStation.pm10.value) {
    return "No CHPC PM10 reading";
  }

  return `${chpcStation.pm10.value} ${chpcStation.pm10.unit || "µg/m³"}`;
}

function findMatchingStation(site, liveStations) {
  if (!liveStations || !Array.isArray(liveStations)) return null;

  if (site.station_key) {
    const exact = liveStations.find(
      (station) => station.name === site.station_key,
    );
    if (exact) return exact;
  }

  const siteName = normalizeName(site.name);
  const siteKey = normalizeName(site.station_key);

  return liveStations.find((station) => {
    const stationName = normalizeName(station.name);

    return (
      stationName === siteKey ||
      stationName === siteName ||
      stationName.includes(siteKey) ||
      stationName.includes(siteName) ||
      siteName.includes(stationName)
    );
  });
}

function findMatchingChpcStation(site, chpcStations) {
  if (!site || !chpcStations || !Array.isArray(chpcStations)) return null;

  const siteKey = normalizeName(site.station_key);
  const siteName = normalizeName(site.name);

  const possibleNames = [siteKey, siteName].filter((name) => name.length > 2);

  if (possibleNames.length === 0) return null;

  return chpcStations.find((station) => {
    const stationName = normalizeName(station.name);
    const stationCode = normalizeName(station.station_code);

    return possibleNames.some((name) => {
      return (
        stationName === name ||
        stationCode === name ||
        stationName.includes(name) ||
        name.includes(stationName)
      );
    });
  });
}

function findChpcForLiveStation(station, chpcStations) {
  if (!station || !chpcStations || !Array.isArray(chpcStations)) return null;

  const stationName = normalizeName(station.name);

  const directMatches = {
    roosevelt: "QRS",
    vernal: "QV4",
    duchesne: "A1388",
    fruitland: "A1388",
    myton: "A1388",
    "south ouray": "A1622",
    "north uintah basin": "A1386",
    "red wash": "A1633",
    horsepool: "A1633",
  };

  const stationCode = directMatches[stationName];

  if (stationCode) {
    const byCode = chpcStations.find(
      (chpc) => chpc.station_code === stationCode,
    );

    if (byCode) return byCode;
  }

  return chpcStations.find((chpc) => {
    const chpcName = normalizeName(chpc.name);

    return (
      chpcName === stationName ||
      chpcName.includes(stationName) ||
      stationName.includes(chpcName)
    );
  });
}

// =======================
// FACILITIES
// =======================

safeFetchJson("geoJson/facilities.geojson", "Facilities GeoJSON")
  .then((data) => {
    facilitiesGeoJsonLayer = L.geoJSON(data, {
      pointToLayer: function (feature, latlng) {
        return L.circleMarker(latlng, {
          radius: 8,
          color: "purple",
          fillColor: "yellow",
          fillOpacity: 0.8,
          weight: 2,
        });
      },

      onEachFeature: function (feature, layer) {
        const props = feature.properties || {};

        layer.bindPopup(`
          <strong>${getValue(props.name, "Facility")}</strong><br><br>
          <strong>Type:</strong> ${getValue(props.type)}<br>
          <strong>Industry:</strong> ${getValue(props.industry)}<br>
          <strong>Status:</strong> ${getValue(props.status)}<br>
          <strong>County:</strong> ${getValue(props.county)}
        `);
      },
    }).addTo(map);

    console.log("Facilities loaded");
  })
  .catch((error) => console.error("Facilities loading error:", error));

// =======================
// COMPLAINTS
// =======================

safeFetchJson("archive/data/complaints.json", "Complaints")
  .then((complaints) => {
    console.log("Complaints loaded:", complaints);

    complaints.forEach((complaint) => {
      if (!complaint.lat || !complaint.lng) return;

      const marker = L.marker([complaint.lat, complaint.lng]).addTo(map);
      complaintMarkers.push(marker);

      marker.bindPopup(`
        <strong>${getValue(complaint.type, "Complaint")}</strong><br><br>
        ${complaint.description || ""}<br><br>
        <strong>Date:</strong> ${getValue(complaint.date)}<br>
        <strong>County:</strong> ${getValue(complaint.county)}<br>
        <strong>Source:</strong> ${getValue(complaint.source)}<br>
        <strong>Category:</strong> ${getValue(complaint.category)}<br>
        <strong>Industry:</strong> ${getValue(complaint.industry)}
      `);
    });

    buildComplaintChart(complaints);
    loadAirQualityCharts();
    loadDEQIncidentCharts();
  })
  .catch((error) => console.error("Complaint loading error:", error));

// =======================
// DEQ INCIDENTS
// =======================

function getDEQIncidentColor(type) {
  if (type === "Produced Water Release") return "#7b3f98";
  if (type === "Oil Spill") return "#4b2e2b";
  if (type === "H2S Release") return "#d00000";
  if (type === "Chemical Release") return "#8e44ad";
  if (type === "Hydraulic Oil Leak") return "#6c5ce7";
  if (type === "Wastewater Release") return "#2980b9";
  if (type === "Mercury Incident") return "#34495e";
  if (type === "Fuel Spill") return "#e67e22";
  return "#9b59b6";
}

safeFetchJson("archive/data/deq_incidents_2016_present.json", "DEQ Incidents")
  .then((incidents) => {
    console.log("DEQ incidents loaded:", incidents);

    incidents.forEach((incident) => {
      if (!incident.lat || !incident.lng) return;

      const color = getDEQIncidentColor(incident.type);

      const marker = L.circleMarker([incident.lat, incident.lng], {
        radius: 5,
        color: color,
        fillColor: color,
        fillOpacity: 0.65,
        weight: 1,
      }).addTo(map);

      deqIncidentMarkers.push(marker);

      marker.bindPopup(`
        <strong>${getValue(incident.type, "DEQ Incident")}</strong><br><br>
        <strong>Title:</strong> ${getValue(incident.title)}<br>
        <strong>Date:</strong> ${getValue(incident.date)}<br>
        <strong>County:</strong> ${getValue(incident.county)}<br>
        <strong>Company:</strong> ${getValue(incident.company)}<br>
        <strong>Nearest City:</strong> ${getValue(incident.nearest_city)}<br>
        <strong>Address/Location:</strong> ${getValue(incident.address)}<br><br>
        ${incident.description || ""}<br><br>
        <strong>Source:</strong> ${getValue(incident.source)}
      `);
    });
  })
  .catch((error) => console.error("DEQ incident loading error:", error));

// =======================
// HISTORICAL DEQ INCIDENTS 2007-2015
// =======================

function getHistoricalDEQColor(type) {
  if (type === "Produced Water Release") return "#b084cc";
  if (type === "Oil Spill") return "#8d6e63";
  if (type === "H2S Release") return "#d98880";
  if (type === "Chemical Release") return "#bb8fce";
  if (type === "Hydraulic Oil Leak") return "#a29bfe";
  if (type === "Wastewater Release") return "#85c1e9";
  if (type === "Mercury Incident") return "#95a5a6";
  if (type === "Fuel Spill") return "#f5b041";
  return "#c39bd3";
}

safeFetchJson(
  "archive/data/deq_incidents_pre2016.json",
  "Historical DEQ Incidents",
)
  .then((incidents) => {
    console.log("Historical DEQ incidents loaded:", incidents);

    incidents.forEach((incident) => {
      if (!incident.lat || !incident.lng) return;

      const color = getHistoricalDEQColor(incident.type);

      const marker = L.circleMarker([incident.lat, incident.lng], {
        radius: 4,
        color: color,
        fillColor: color,
        fillOpacity: 0.4,
        weight: 1,
      });

      historicalDEQMarkers.push(marker);

      marker.bindPopup(`
        <strong>Historical: ${getValue(incident.type, "DEQ Incident")}</strong><br><br>
        <strong>Title:</strong> ${getValue(incident.title)}<br>
        <strong>Date:</strong> ${getValue(incident.date)}<br>
        <strong>County:</strong> ${getValue(incident.county)}<br>
        <strong>Company:</strong> ${getValue(incident.company)}<br>
        <strong>Nearest City:</strong> ${getValue(incident.nearest_city)}<br>
        <strong>Address/Location:</strong> ${getValue(incident.address)}<br><br>
        ${incident.description || ""}<br><br>
        <strong>Source:</strong> ${getValue(incident.source)}
      `);
    });
  })
  .catch((error) =>
    console.error("Historical DEQ incident loading error:", error),
  );

// =======================
// COMPLAINT GRAPH
// =======================

function getYearsFrom2016ThroughNextYear() {
  const currentYear = new Date().getFullYear();
  const years = [];

  for (let year = 2016; year <= currentYear + 1; year++) {
    years.push(String(year));
  }

  return years;
}

function getYearFromDate(dateValue) {
  if (!dateValue) return null;

  const match = String(dateValue).match(/(19|20)\d{2}/);

  return match ? match[0] : null;
}

function buildComplaintChart(complaints) {
  const complaintChart = document.getElementById("complaintChart");

  if (!complaintChart || typeof Chart === "undefined") return;

  const years = getYearsFrom2016ThroughNextYear();
  const currentYear = String(new Date().getFullYear());
  const nextYear = String(new Date().getFullYear() + 1);

  const yearlyCounts = {};

  years.forEach((year) => {
    yearlyCounts[year] = 0;
  });

  complaints.forEach((complaint) => {
    const year = getYearFromDate(complaint.date);

    if (!year || Number(year) < 2016) return;

    yearlyCounts[year] = (yearlyCounts[year] || 0) + 1;
  });

  const labels = years.map((year) => {
    if (year === currentYear) return `${year} YTD (${yearlyCounts[year]})`;
    if (year === nextYear) return `${year} projected`;
    return `${year} (${yearlyCounts[year]})`;
  });

  const counts = years.map((year) => {
    if (year === nextYear) return null;

    return yearlyCounts[year];
  });

  new Chart(complaintChart, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Environmental Complaints",
          data: counts,
          borderColor: "#ff4444",
          backgroundColor: "rgba(255,68,68,0.2)",
          tension: 0.3,
          fill: true,
          spanGaps: false,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
    },
  });
}
function buildDEQIncidentChart(currentIncidents, historicalIncidents) {
  const chart = document.getElementById("deqIncidentChart");

  if (!chart || typeof Chart === "undefined") return;

  const currentYear = new Date().getFullYear();
  const nextYear = currentYear + 1;
  const years = [];

  for (let year = 2007; year <= 2020; year++) {
    years.push(String(year));
  }

  const historicalCounts = {};
  const currentCounts = {};

  years.forEach((year) => {
    historicalCounts[year] = 0;
    currentCounts[year] = 0;
  });

  historicalIncidents.forEach((incident) => {
    const year = getYearFromDate(incident.date);
    if (year && Number(year) < 2016) {
      historicalCounts[year] = (historicalCounts[year] || 0) + 1;
    }
  });

  currentIncidents.forEach((incident) => {
    const year = getYearFromDate(incident.date);
    if (year && Number(year) >= 2016) {
      currentCounts[year] = (currentCounts[year] || 0) + 1;
    }
  });

  const labels = years.map((year) => {
    return year;
  });

  const historicalData = years.map((year) => {
    if (Number(year) >= 2016 || Number(year) === nextYear) return null;
    return historicalCounts[year];
  });

  const currentData = years.map((year) => {
    if (Number(year) < 2016 || Number(year) === nextYear) return null;
    return currentCounts[year];
  });

  new Chart(chart, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Historical DEQ Incidents 2007–2015",
          data: historicalData,
          backgroundColor: "rgba(177, 132, 204, 0.55)",
        },
        {
          label: "DEQ Incidents 2016–2020 OpenData Archive",

          data: currentData,
          backgroundColor: "rgba(123, 63, 152, 0.75)",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
    },
  });
}

function loadDEQIncidentCharts() {
  Promise.all([
    safeFetchJson(
      "archive/data/deq_incidents_2016_present.json",
      "DEQ Current Incidents",
    ),
    safeFetchJson(
      "archive/data/deq_incidents_pre2016.json",
      "DEQ Historical Incidents",
    ),
  ])
    .then(([currentIncidents, historicalIncidents]) => {
      buildDEQIncidentChart(currentIncidents, historicalIncidents);
    })
    .catch((error) => {
      console.error("DEQ incident chart loading error:", error);
    });
}
// =======================
// AIR QUALITY GRAPHS
// =======================

function loadAirQualityCharts() {
  safeFetchJson("archive/data/airQuality.json", "Air Quality")
    .then((records) => {
      buildAirQualityChart(
        records,
        "ozoneChart",
        "Ozone",
        "ozone_ppb",
        "ppb",
        70,
      );
      buildAirQualityChart(records, "pm25Chart", "PM2.5", "pm25", "µg/m³", 12);
      buildAirQualityChart(records, "pm10Chart", "PM10", "pm10", "µg/m³", 150);
    })
    .catch((error) => {
      console.error("Air quality chart loading error:", error);
    });
}

function buildAirQualityChart(records, canvasId, label, field, unit, standard) {
  const canvas = document.getElementById(canvasId);

  if (!canvas || typeof Chart === "undefined") return;

  const filtered = records
    .filter(
      (record) =>
        record.date && record[field] !== null && record[field] !== undefined,
    )
    .sort((a, b) => new Date(a.date) - new Date(b.date));

  const labels = filtered.map((record) => {
    const date = new Date(record.date);

    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  });

  const values = filtered.map((record) => Number(record[field]));

  new Chart(canvas, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: `${label} (${unit})`,
          data: values,
          borderColor: "#c96f3d",
          backgroundColor: "rgba(201, 111, 61, 0.18)",
          tension: 0.3,
          fill: true,
        },
        {
          label: `Health Standard (${standard} ${unit})`,
          data: Array(values.length).fill(standard),
          borderColor: "#6f4058",
          borderDash: [6, 6],
          pointRadius: 0,
          fill: false,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
    },
  });
}

// =======================
// WELLS
// =======================

safeFetchJson("archive/data/wells.json", "Wells")
  .then((wells) => {
    console.log("Wells loaded:", wells);

    wells.forEach((well) => {
      if (!well.lat || !well.lng) return;

      const marker = L.circleMarker([well.lat, well.lng], {
        radius: 6,
        color: "black",
        fillColor: "orange",
        fillOpacity: 0.8,
      }).addTo(map);

      wellMarkers.push(marker);

      marker.bindPopup(`
        <strong>${getValue(well.name, "Well")}</strong><br><br>
        <strong>Operator:</strong> ${getValue(well.operator)}<br>
        <strong>Status:</strong> ${getValue(well.status)}<br>
        <strong>County:</strong> ${getValue(well.county)}<br>
        <strong>Year:</strong> ${getValue(well.year)}
      `);
    });
  })
  .catch((error) => console.error("Well loading error:", error));

// =======================
// H2S REPORTS
// =======================

safeFetchJson("archive/data/h2s.json", "H2S")
  .then((reports) => {
    console.log("H2S loaded:", reports);

    reports.forEach((report) => {
      if (!report.lat || !report.lng) return;

      const marker = L.circleMarker([report.lat, report.lng], {
        radius: 10,
        color: "darkred",
        fillColor: "red",
        fillOpacity: 0.8,
      }).addTo(map);

      h2sMarkers.push(marker);

      marker.bindPopup(`
        <strong>${getValue(report.type, "H2S Report")}</strong><br><br>
        ${report.description || ""}<br><br>
        <strong>Severity:</strong> ${getValue(report.severity)}<br>
        <strong>Date:</strong> ${getValue(report.date)}<br>
        <strong>County:</strong> ${getValue(report.county)}
      `);
    });
  })
  .catch((error) => console.error("H2S loading error:", error));

// =======================
// MONITORING SITES + LIVE AQ POPUPS
// =======================

Promise.all([
  safeFetchJson("archive/data/monitoring_sites.json", "Monitoring sites"),
  safeFetchJson("archive/data/live_air_quality.json", "Live AQ"),
  safeFetchJson("archive/data/chpc_live_air_quality.json", "CHPC AQ").catch(
    () => null,
  ),
])
  .then(([sites, liveAQ, chpcAQ]) => {
    console.log("Monitoring sites loaded:", sites);
    console.log("Live AQ loaded for monitor popups:", liveAQ);
    console.log("CHPC AQ loaded for monitor popups:", chpcAQ);

    const liveStations = liveAQ.stations || [];
    const chpcStations = chpcAQ && chpcAQ.stations ? chpcAQ.stations : [];

    sites.forEach((site) => {
      if (!site.lat || !site.lng) return;

      const matchingStation = findMatchingStation(site, liveStations);
      const matchingChpc = findMatchingChpcStation(site, chpcStations);

      const markerColor = getWorstStationColor(matchingStation, matchingChpc);

      const airNowHTML = matchingStation
        ? `
          <div class="popup-reading">
            <strong>Live AirNow Reading</strong><br>
            <strong>AQI:</strong> ${cleanReading(matchingStation.aqi)} (${getAQIStatus(matchingStation.aqi)})<br>
            <strong>Ozone:</strong> ${formatAirNowOzone(matchingStation.ozone)}<br>
            <strong>PM2.5:</strong> ${formatAirNowPM25(matchingStation.pm25)}<br>
            <strong>PM10:</strong> ${formatPM10AQI(matchingStation.pm10)}<br>
            <strong>Updated:</strong> ${liveAQ.updated}
          </div>
        `
        : `
          <div class="popup-reading">
            <strong>AirNow Reading:</strong><br>
            No matching AirNow reading for this site.
          </div>
        `;

      const chpcHTML = matchingChpc
        ? `
          <div class="popup-reading">
            <strong>Live CHPC Reading</strong><br>
            <strong>Ozone:</strong> ${formatChpcOzone(matchingChpc)} (${getOzoneStatusPPBV(matchingChpc.ozone && matchingChpc.ozone.value)})<br>
            <strong>PM2.5:</strong> ${formatChpcPM25(matchingChpc)}<br>
            <strong>PM10:</strong> ${formatChpcPM10(matchingChpc)}<br>
            <strong>Station:</strong> ${matchingChpc.station_code}<br>
            <strong>Updated:</strong> ${matchingChpc.updated}
          </div>
        `
        : `
          <div class="popup-reading">
            <strong>CHPC Reading:</strong><br>
            No matching CHPC reading for this site.
          </div>
        `;

      const marker = L.circleMarker([site.lat, site.lng], {
        radius: 9,
        color: markerColor,
        fillColor: markerColor,
        fillOpacity: 0.85,
        weight: 2,
      }).addTo(map);

      monitoringMarkers.push(marker);

      marker.bindPopup(`
        <strong>${getValue(site.name, "Monitoring Site")}</strong><br><br>
        <strong>Type:</strong> ${getValue(site.type)}<br>
        <strong>County:</strong> ${getValue(site.county)}<br>
        <strong>Measurements:</strong> ${formatMeasurements(site.measurements)}<br>
        <strong>Source:</strong> ${getValue(site.source)}<br>
        <strong>Status:</strong> ${getValue(site.status)}<br><br>
        ${airNowHTML}
        ${chpcHTML}
      `);
    });
  })
  .catch((error) => {
    console.warn("Monitoring sites/live AQ not loaded:", error);
  });

// =======================
// LIVE AQ CARD + REGIONAL CAROUSEL
// =======================

function loadLiveAQ() {
  Promise.all([
    safeFetchJson("archive/data/live_air_quality.json", "Live AQ"),
    safeFetchJson("archive/data/chpc_live_air_quality.json", "CHPC AQ").catch(
      () => null,
    ),
    safeFetchJson(
      "archive/data/monitoring_sites.json",
      "Monitoring Sites",
    ).catch(() => []),
  ])
    .then(([data, chpcAQ, monitoringSites]) => {
      const chpcStations = chpcAQ && chpcAQ.stations ? chpcAQ.stations : [];

      const aqiValue = document.getElementById("aqiValue");
      const ozoneValue = document.getElementById("ozoneValue");
      const pm25Value = document.getElementById("pm25Value");
      const pm10Value = document.getElementById("pm10Value");
      const fireRiskValue = document.getElementById("fireRiskValue");
      const aqUpdated = document.getElementById("aqUpdated");
      const aqiStatus = document.getElementById("aqiStatus");
      const aqiBar = document.getElementById("aqiBar");
      const stationReadings = document.getElementById("stationReadings");

      if (!aqiValue) return;

      const chpcOzoneValues = chpcStations
        .map((station) => Number(station.ozone?.value))
        .filter((value) => !isNaN(value));

      const chpcPM25Values = chpcStations
        .map((station) => Number(station.pm25?.value))
        .filter((value) => !isNaN(value));

      const regionalOzone = chpcOzoneValues.length
        ? Math.max(...chpcOzoneValues)
        : null;

      const regionalPM25 = chpcPM25Values.length
        ? Math.max(...chpcPM25Values)
        : null;

      const airNowPM10Values = (data.stations || [])
        .map((station) => Number(station.pm10))
        .filter((value) => !isNaN(value));

      const regionalPM10AQI = airNowPM10Values.length
        ? Math.max(...airNowPM10Values)
        : null;

      const regionalOzoneStatus = ozoneLevel(regionalOzone);

      aqiValue.textContent =
        regionalOzone === null ? "--" : pollutantBadge(regionalOzoneStatus);

      ozoneValue.textContent =
        regionalOzone === null ? "--" : `${regionalOzone} ppbv`;

      pm25Value.textContent =
        regionalPM25 === null ? "--" : `${regionalPM25} µg/m³`;

      if (pm10Value) {
        pm10Value.textContent =
          regionalPM10AQI === null ? "Data gap" : `AQI ${regionalPM10AQI}`;
      }

      if (fireRiskValue) {
        fireRiskValue.textContent = data.fireRisk ?? "--";
      }

      if (aqUpdated) {
        aqUpdated.textContent = data.updated ?? "Not updated";
      }

      if (stationReadings && monitoringSites) {
        stationReadings.innerHTML = monitoringSites
          .filter((site) => site.lat && site.lng)
          .map((site) => {
            const station = findMatchingStation(site, data.stations || []) || {
              name: site.station_key || site.name,
              aqi: "--",
              ozone: "--",
              pm25: "--",
              pm10: "--",
            };

            const chpcStation =
              findMatchingChpcStation(site, chpcStations) ||
              findChpcForLiveStation(station, chpcStations);

            const color = getWorstStationColor(station, chpcStation);
            const nearestOzoneStation = findNearestChpcWithOzone(
              site,
              chpcStations,
            );

            const siteOzoneValue = chpcStation?.ozone?.value;
            const sitePM25Value = chpcStation?.pm25?.value;
            const sitePM10Value = chpcStation?.pm10?.value;

            const ozoneStatus = ozoneLevel(siteOzoneValue);
            const pm25Status = pm25Level(sitePM25Value);
            const pm10Status = pm10Level(sitePM10Value);

            return `
              <div class="station-pill">
                <div class="station-dot" style="background:${color};"></div>

                <div class="station-info">
                  <strong>${site.name}</strong>

                  <div>${
                    chpcStation
                      ? "CHPC Ozone Monitor"
                      : station.aqi === "--"
                        ? "Monitoring Gap"
                        : `AirNow AQI ${station.aqi}`
                  }</div>

                  <small class="monitor-note">
                    ${
                      chpcStation
                        ? "CHPC monitor reporting live pollutant concentration"
                        : station.aqi === "--"
                          ? "⚪ Monitoring gap — needs local data source"
                          : "AirNow AQI is an index, not concentration"
                    }
                  </small>

                  <small>
                    Ozone:
                    ${
                      siteOzoneValue
                        ? `${siteOzoneValue} ppbv · ${pollutantBadge(ozoneStatus)}`
                        : nearestOzoneStation
                          ? `${nearestOzoneStation.ozone.value} ppbv · nearest CHPC monitor: ${nearestOzoneStation.name} (${Math.round(nearestOzoneStation.distanceMiles)} mi)`
                          : "⚪ No Local Monitor"
                    }
                  </small>

                  <small>
                    PM2.5:
                    ${
                      sitePM25Value
                        ? `${sitePM25Value} µg/m³ · ${pollutantBadge(pm25Status)}`
                        : station.pm25 !== "--" &&
                            station.pm25 !== null &&
                            station.pm25 !== undefined
                          ? `AQI ${station.pm25} · AirNow nearest monitor`
                          : "⚪ No local PM2.5 monitor"
                    }
                  </small>

                  <small>
                    PM10:
                    ${
                      sitePM10Value
                        ? `${sitePM10Value} µg/m³ · ${pollutantBadge(pm10Status)}`
                        : station.pm10 !== "--" &&
                            station.pm10 !== null &&
                            station.pm10 !== undefined
                          ? `AQI ${station.pm10} · AirNow nearest monitor`
                          : regionalPM10AQI !== null
                            ? `Regional AQI ${regionalPM10AQI} · nearest AirNow reading`
                            : "⚪ No PM10 monitor connected"
                    }
                  </small>
                </div>
              </div>
            `;
          })
          .join("");
      }

      if (aqiBar && aqiStatus) {
        const width =
          regionalOzone === null
            ? 0
            : Math.min((regionalOzone / 70) * 100, 100);

        const color = getPollutantColorFromStatus(
          getOzoneStatusPPBV(regionalOzone),
        );

        aqiBar.style.width = width + "%";
        aqiBar.style.background = color;
        aqiStatus.textContent =
          regionalOzone === null
            ? "No CHPC regional ozone reading"
            : `Regional ozone status based on CHPC monitors (${regionalOzone} ppbv)`;
      }
    })
    .catch((error) => {
      console.warn("Live AQ unavailable:", error);

      const aqUpdated = document.getElementById("aqUpdated");

      if (aqUpdated) {
        aqUpdated.textContent = "Live AQ unavailable";
      }
    });
}

loadLiveAQ();
setInterval(loadLiveAQ, 300000);

//===MAP KEY LEGEND===//

const mapLegend = L.control({ position: "topright" });

mapLegend.onAdd = function () {
  const div = L.DomUtil.create("div", "map-legend");

  div.innerHTML = `
    <strong>Map Key</strong>
    <div><span class="legend-dot complaint-dot"></span> Complaint</div>
    <div><span class="legend-dot monitor-low"></span> Low / Connected monitor</div>
    <div><span class="legend-dot monitor-watch"></span> Moderate / Watch</div>
    <div><span class="legend-dot monitor-high"></span> High ozone / concern</div>
    <div><span class="legend-dot monitor-gap"></span> Data gap / research site</div>
    <div><span class="legend-dot well-dot"></span> Well</div>
    <div><span class="legend-dot h2s-dot"></span> H₂S report</div>
  `;

  return div;
};

mapLegend.addTo(map);

// =======================
// TOGGLES
// =======================

function toggleComplaints() {
  complaintsVisible = !complaintsVisible;

  complaintMarkers.forEach((marker) => {
    complaintsVisible ? marker.addTo(map) : map.removeLayer(marker);
  });
}

function toggleFacilities() {
  facilitiesVisible = !facilitiesVisible;

  if (!facilitiesGeoJsonLayer) return;

  facilitiesVisible
    ? facilitiesGeoJsonLayer.addTo(map)
    : map.removeLayer(facilitiesGeoJsonLayer);
}

function toggleWells() {
  wellsVisible = !wellsVisible;

  wellMarkers.forEach((marker) => {
    wellsVisible ? marker.addTo(map) : map.removeLayer(marker);
  });
}

function toggleH2S() {
  h2sVisible = !h2sVisible;

  h2sMarkers.forEach((marker) => {
    h2sVisible ? marker.addTo(map) : map.removeLayer(marker);
  });
}

function toggleDEQIncidents() {
  deqIncidentsVisible = !deqIncidentsVisible;

  deqIncidentMarkers.forEach((marker) => {
    deqIncidentsVisible ? marker.addTo(map) : map.removeLayer(marker);
  });
}

function toggleHistoricalDEQ() {
  historicalDEQVisible = !historicalDEQVisible;

  historicalDEQMarkers.forEach((marker) => {
    historicalDEQVisible ? marker.addTo(map) : map.removeLayer(marker);
  });
}

function toggleMonitoring() {
  monitoringVisible = !monitoringVisible;

  monitoringMarkers.forEach((marker) => {
    monitoringVisible ? marker.addTo(map) : map.removeLayer(marker);
  });
}

function toggleParcels() {
  parcelsVisible = !parcelsVisible;

  parcelsVisible ? parcels.addTo(map) : map.removeLayer(parcels);
}

function toggleGraphs() {
  const graphSection = document.getElementById("graphSection");

  if (graphSection) {
    graphSection.scrollIntoView({
      behavior: "smooth",
    });
  }
}

// =======================
// PAGE NAVIGATION
// =======================

function openResearch() {
  window.location.href = "pages/research.html";
}

function openArchive() {
  window.location.href = "pages/archive.html";
}

function openUpdates() {
  window.location.href = "pages/updates.html";
}
