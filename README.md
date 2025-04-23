# gpx-viewer


Demo: https://gpxviewr.genannt.name/


## development

For development devcontainers are used.

#### celery worker

```
cd gpxviewr/
celery -A gpxviewr worker -l INFO -B
```

#### development webserver

```
cd gpxviewr/
./manage.py loaddata baseweb/fixtures/gpx_waypoint_type.yaml 
./manage.py runserver
```

#### webpack

```
cd frontend
npm run dev
```

#### Valhalla Routing Server

The valhalla routing server needs the Valhalla tiles inside the directory `valhalla-data`.

You can generate the routing information (tiles) with Valhalla.
See: https://valhalla.github.io/valhalla/building/#running-valhalla-server-on-unix
