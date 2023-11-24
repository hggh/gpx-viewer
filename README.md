# gpx-viewer


Demo: https://gpxviewr.genannt.name/gpxtrack/agaxdfkIoP5msdVKgNxtSjx9qz9yqWPICbzUkKyh


## development

docker compose up -d


run celery:

celery -A gpxviewr worker -l INFO -B

run webserver:

./manage.py runserver
