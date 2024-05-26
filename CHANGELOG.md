# CHANGELOG

### 25. May 2024

  * fix performance; do not create split markers on overy almost over move
  * fix user segment delete with update the other
  * user splits now with click on the polyline without extra markers
  * hide/show elevation graph
  * hide next/pre buttons if only one track exists
  * nice icons for hide/show elevation graph

### 12. May 2024

  * place POI button on the right
  * remove integrity after update of bootstrap
  * update Demo Track handling via settings
  * add split track feature nicer way - delete is broken yet
  * nicer elevation graph

### 26. March 2024

  * remove Track Split feature - UI is not very good
  * add almostOver Leaflet Plugin to have a better hover
  * better D3.js Graph with hover support on map and elevation graph
  * Django Upgrade to 5.0.3
  * place marker on track lat/lon
  * Bootstrap Upgrade to 5.3.3
  * move elevation graph to map
  * move list of POIs to a overlay offcanvas
  * move download of POIs to a overlay offcanvas
  * if ele is None set it to 0

### 22. January 2024

  * if empty trkseg or too few points inside a trkseg - no query is possible - do not query

### 18. January 2024

  * use tag contact:website and website tag for getting url from OSM data

### 14. January 2024

  * allow Download Track split
  * pregenerate Elevation Graph data (perhaps later do it in the Browser?)
  * add og Meta information

### 13. January 2024

  * fix popupop if html id is yet missing
  * add django-cors-headers
  * elevation Graph with D3js
  * bounce marker if mouseover table / element
  * Marker = rot

### 08. January 2024

  * fix typo index.html
  * Update to Django 5.0.1
  * Query Google Maps (Link to Google Maps, for StreetView, ...)
  * generate GEOJson Line from database not from GPX File to have DB IDs within
  * add elevation (from GPXTrack file) uphill, downhill
  * add Markers for the points of the line to enable splitting and co (show only current bounding box, on zoom)
  * basic Splitten feature, needs UI work

### 27. December 2023

  * show all tag infos from OSM
  * only allow Road type bike for Valahalle Routing Engine
  * add note on start page

### 26. December 2023

  * updated robots.txt
  * add Valhalla Infos and docker container inside docker-compose file
  * away kilometer as int
  * bounce Marker if "on map" is clicked

### 20. December 2023

  * only accept *.gpx files on file upload
  * after finding the air-line distance nearest track point from the POI
    we query Valhalla Routing Engine with the 100 points before and after the air-line point
    after we have the "best" point for street routing, we calculate the route and safe the
    geojson.
  * query for biketype for Valhalla Routing - currently not used.
  * set map height to 600px
  * show distance from track to POI in km

### 11. December 2023

  * Valhalla Routing Engine
  * Download GPX Track to POI from nearest point of the track
  * add POI apartment/guest_house/hostel/hotel/motel

### 5. December 2023

 * Django 5.0
 * working on layout
 * sort Waypoints in order of the track
 * add different colors for Tracks / Segments
 * Leaflet Track line via geojson ajax call (faster)

### 1. December 2023

 * list your uploaded tracks on the Upload Page
 * nicer waiting spinner
 * show waypoints while job is query running
 * autoreload page then job is finished

### 29. November 2023

 * add URL to GPX Waypoint file if it's available in OSM
 * find and show supermarket and convenience on map
 * OpenStreetMap Map Query - link with correct zoomlevel on map
 * show/hide itmes on map: nicer position
 * show/hide POIs on map and export
 * zoom map to POI in list
 * new layout

### 24. November 2023

 * use XMLHttpRequest to get waypoint information to generate it in JavaScript
 * show / hide Marks on Map

### 24. November 2023

 * add fuel/gas station
 * filter out duplicates within range of meters (per item setting by user)
 * add links to Github Changelog
 * add bootstrap Icons
 * job to delete GPX Track (default 10 days, user can setup it)
 * send 2000 lat/lon points from track to OSM Overpass API instead of 1000 per batch
 
