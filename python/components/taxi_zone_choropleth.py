import json
import streamlit.components.v1 as components
import streamlit as st


HTML_TEMPLATE = """
<div id="map-wrap">
  <svg
    id="taxi-zone-map"
    viewBox="0 0 720 560"
    aria-label="NYC taxi pickup zones"
  ></svg>

  <div id="taxi-zone-tooltip"></div>

  <div class="map-credit">
    Rendered with D3.js · © 2026 Michael Lockwood
  </div>
</div>

<style>
  body {
    margin: 0;
    background: transparent;
  }

  #taxi-zone-map {
    display: block;
    width: 100%;
    height: auto;
  }

  #taxi-zone-tooltip {
    position: absolute;
    pointer-events: none;
    opacity: 0;
    padding: 6px 8px;
    border-radius: 6px;
    background: rgba(0, 0, 0, 0.85);
    color: white;
    font: 12px/1.4 system-ui, sans-serif;
    white-space: nowrap;
  }
  
  #map-wrap {
    position: relative;
    width: 100%;
  }

  .taxi-zone {
    stroke: orange;
    stroke-width: 0.5;
    vector-effect: non-scaling-stroke;
  }
</style>

<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>

<script>
  const raw = __GEOJSON__;

  function sampleCoordinates(geometry, output) {
    if (!geometry) {
      return;
    }

    if (geometry.type === "Point") {
      output.push(geometry.coordinates);
    }

    if (
      geometry.type === "MultiPoint" ||
      geometry.type === "LineString"
    ) {
      output.push(...geometry.coordinates);
    }

    if (geometry.type === "MultiLineString") {
      geometry.coordinates.forEach(
        line => output.push(...line)
      );
    }

    if (geometry.type === "Polygon") {
      geometry.coordinates.forEach(
        ring => output.push(...ring)
      );
    }

    if (geometry.type === "MultiPolygon") {
      geometry.coordinates.forEach(
        polygon => polygon.forEach(
          ring => output.push(...ring)
        )
      );
    }
  }

  function coordinatesAreSwapped(coordinates) {
    const sampleSize = Math.min(coordinates.length, 500);
    let swappedCount = 0;

    for (let index = 0; index < sampleSize; index++) {
      const [first, second] = coordinates[index];

      if (
        first > 24 &&
        first < 50 &&
        second < -60 &&
        second > -90
      ) {
        swappedCount++;
      }
    }

    return swappedCount / sampleSize > 0.6;
  }

  function swapGeometryCoordinates(geometry) {
    if (!geometry) {
      return;
    }

    const swapRingCoordinates = rings =>
      rings.map(
        ring => ring.map(
          ([latitude, longitude]) => [longitude, latitude]
        )
      );

    switch (geometry.type) {
      case "Point":
        geometry.coordinates = [
          geometry.coordinates[1],
          geometry.coordinates[0]
        ];
        break;

      case "MultiPoint":
      case "LineString":
        geometry.coordinates = geometry.coordinates.map(
          ([latitude, longitude]) => [longitude, latitude]
        );
        break;

      case "MultiLineString":
        geometry.coordinates = geometry.coordinates.map(
          line => line.map(
            ([latitude, longitude]) => [longitude, latitude]
          )
        );
        break;

      case "Polygon":
        geometry.coordinates = swapRingCoordinates(
          geometry.coordinates
        );
        break;

      case "MultiPolygon":
        geometry.coordinates = geometry.coordinates.map(
          polygon => swapRingCoordinates(polygon)
        );
        break;
    }
  }

  const sampledCoordinates = [];

  raw.features.forEach(
    feature => sampleCoordinates(
      feature.geometry,
      sampledCoordinates
    )
  );

  if (
    sampledCoordinates.length &&
    coordinatesAreSwapped(sampledCoordinates)
  ) {
    raw.features.forEach(
      feature => swapGeometryCoordinates(feature.geometry)
    );
  }

  const svg = d3.select("#taxi-zone-map");
  const tooltip = d3.select("#taxi-zone-tooltip");
  const width = 720;
  const initialHeight = 560;

  const projection = d3
    .geoMercator()
    .fitSize([width, initialHeight], raw);

  const path = d3.geoPath(projection);
  const bounds = path.bounds(raw);

  const padding = 12;

  const x0 = bounds[0][0] - padding;
  const y0 = bounds[0][1] - padding;
  const x1 = bounds[1][0] + padding;
  const y1 = bounds[1][1] + padding;

  svg.attr(
    "viewBox",
    `${x0} ${y0} ${x1 - x0} ${y1 - y0}`
  );

  const tripCount = feature =>
    Number(feature.properties.TripCount ?? 0);

  const maximumTrips =
    d3.max(raw.features, tripCount) || 1;

  const color = d3
    .scaleSequential(
      t => d3.interpolateBlues(0.25 + t * 0.75)
    )
    .domain([0, Math.sqrt(maximumTrips)]);

  svg
    .selectAll("path")
    .data(raw.features)
    .join("path")
    .attr("class", "taxi-zone")
    .attr("d", path)
    .attr(
      "fill",
      feature => color(
        Math.sqrt(tripCount(feature))
      )
    )
    .on("mousemove", (event, feature) => {
      const properties = feature.properties || {};

      const borough = properties.Borough ?? "";
      const zone = properties.Zone ?? "Unknown zone";
      const trips = Number(
        properties.TripCount ?? 0
      ).toLocaleString("en-US");

      tooltip
        .style("left", `${event.offsetX + 12}px`)
        .style("top", `${event.offsetY - 28}px`)
        .style("opacity", 1)
        .html(
          `<strong>${borough}</strong><br>` +
          `${zone}<br>` +
          `Trips: ${trips}`
        );
    })
    .on("mouseleave", () => {
      tooltip.style("opacity", 0);
    });
</script>
"""


def render_taxi_zone_choropleth(
    taxi_zones_geojson: dict,
    height: int = 560,
) -> None:
    geojson_json = json.dumps(taxi_zones_geojson)

    map_html = HTML_TEMPLATE.replace(
        "__GEOJSON__",
        geojson_json,
    )

    st.iframe(
        map_html,
        width="stretch",
        height=height,
    )