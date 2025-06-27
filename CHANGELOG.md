# CHANGELOG

### 27. June 2025
  * better download of track with POIs

### 25. June 2025
  * max zoom again 19
  * garmin vs orginal position of Waypoint added
  * OSM Map FR

### 23. June 2025
  * fix footer
  * allow GPX Split Download with Waypoints
  * bookmark Waypoints
  * nicer copy to clipboard popover with BS Toast
  * add Hillshade Overlay Map
  * changed color of Toast

### 20. June 2025
  * Mark camp sites with group_only=yes and permanent_camping=only with red
  * Add Login for GPX Viewer via Github and Strava

### 15. June 2025
  * e bike charging stations: remove access = yes; if station is access=yes display it in green
  * add bakery shops to query

### 8. May 2025
  * Update django-extensions, celery
  * Update Django
  * allow to show/hide POIs inside Map
  * allow to query e bike charging stations: access = yes,amenity = charging_station,bicycle = yes
  * load fixtures on start of application

### 3. May 2025
  * Optimize Layout: Map is no without padding left,right
  * Fix Split Track with Chrome

### 1. May 2025
  * add blue marker for splitting on track

### 26. April 2025
  * Complete new Track Splitting with JavaScript in Realtime with preview on Map
  * fix robots.txt
  * show split button only on TRack View
  * hide text on button on smaller screens
  * optimize layout for smaller screens

### 23. April 2025
  * update README
  * fuel station change around_max to 1000

### 22. April 2025
  * disable /admin Interface
  * more space for map; move filename/track title into header
  * Change GPX Library to gpxpy to fix import problems with some GPXTracks

### 18. April 2025
  * Store Around, around_duplicate and checked Waypoint Type settings into Browser localStore
    * provide a reset to defaults
    * load saved values on pageload to have the older values from user
  * rename bikes to Bike Shops

### 17. April 2025
  * show kilometers on track also on hover on elevation graph
  * reorg index.js and index.html; no js error on startpage
  * Add Query for bicycle Shops

### 16. April 2025
  * try to catch OverpassTooManyRequests error and sleep after it 5sec and retry it
  * show Google Maps link from Waypoint Popup
  * add link to copy geo location of an Waypoint inside the Popup

### 14. April 2025
  * Django Upgrade to 5.2
  * allow 200 chars as GPX Filename
  * strip gpx name and gpx track name over 200 chars; prevent databaseerrors
  * show kilometers on WayPoint Popup (from split start, from track segment start)
  * limit Track Name on elevation Graph to 55 chars.
  * change waypoint icons to SVG
  * allow size change of Waypoint icons via range
  * show tooltip kilometer of track inside Map

### 22. March 2025
  * Django DB Migration on Startup
  * make contact:phone tag also as tel: link
  * internal reorg of models into files
  * Django 5.1.7 Upgrade
  * GPX Track Link with Hostname
  * fix return for gatewaytimeout from overpass

### 1. March 2025
  * handle Overpass Server Load too high - retry it after 4 seconds
  * parse "url" tag as website
  * make phone tags clickable via tel:
  * brouter files have a link inside, parse first link with href element and display it
  * Django 5.1.6

### 12. Feb 2025
  * better Exception handling, output complete traceback into docker logs

### 9. Feb 2025
  * Status API
  * if GPX file is broken, inform user
  * fix delete Split File
  * fix Elevation Graph if more segments and tracks inside a GPX File exists
  * show Waypoint info in the Popup instead in canvas.
  * geojson to 3.2.0
  * django-cors-headers to 4.7.0

### 17. Jan 2025

  * change to webpack for JS/CSS

### 15. Jan 2025

  * new layout - more mobile friendly
  * Django to 5.1.5

### 7. Jan 2025

  * add shelter_type ~ lean_to|weather_shelter

### 16. Jul 2024

  * Django, DjangoRestFramework, Celery Update
  * update gpx python library to create Garmin compatible GPX Tracks

### 10. Jun 2024

  * show track split table only if split exists
  * change default preselected OSM query

### 8. Jun 2024

  * change color of first track/segment in Map
  * fix download of GPX Tracks (content type was on wrong on firefox mobile)

### 4. Jun 2024

  * hover over track split - zoom to track and highlight it in green
  * disable split button after press

### 26. May 2024

  * show delete info on track page
  * show nice info if track file is deleted

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
 
