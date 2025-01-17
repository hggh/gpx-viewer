# gpx-viewer


Demo: https://gpxviewr.genannt.name/


## development

#### Python setup

```
virtualenv -p python3 .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

#### Postgres + Redis
```
docker compose -f docker-compose-dev.yml up -d
```

#### celery worker
```
celery -A gpxviewr worker -l INFO -B
```

#### development webserver
```
./manage.py runserver
```


#### webpack

```
npm run dev
```

#### Valhalla Routing Server

The valhalla routing server needs the Valhalla tiles inside the directory `valhalla-data`.

You can generate the routing information (tiles) with Valhalla.
See: https://valhalla.github.io/valhalla/building/#running-valhalla-server-on-unix
