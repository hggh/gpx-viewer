# gpx-viewer


Demo: https://gpxviewr.genannt.name/gpxtrack/agaxdfkIoP5msdVKgNxtSjx9qz9yqWPICbzUkKyh


## development

#### Python setup

```
virtualenv -p python3 .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

#### Postgres + Redis
```
docker compose up -d
```

#### celery worker
```
celery -A gpxviewr worker -l INFO -B
```

#### development webserver
```
./manage.py runserver
```