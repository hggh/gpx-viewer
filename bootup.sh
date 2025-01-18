#!/usr/bin/env bash

if [[ "$GPX_VIEWR_BOOT_MODE" == "web" ]]; then
    ./manage.py collectstatic --no-input
    gunicorn --capture-output -b 0.0.0.0:8000 -w ${GUNICORN_WORKERS:-5} --threads ${GUNICORN_THREADS:-5} gpxviewr.wsgi:application
elif [[ "$GPX_VIEWR_BOOT_MODE" == "celery" ]]; then
    celery -A gpxviewr worker --loglevel=INFO -B
else
    echo "GPX_VIEWR_BOOT_MODE not known: $GPX_VIEWR_BOOT_MODE"
fi
