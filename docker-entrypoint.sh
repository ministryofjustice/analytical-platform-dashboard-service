#!/bin/bash
ADDRESS=${ADDRESS:-"0.0.0.0"}
PORT=${PORT:-"8000"}
WORKERS=${WORKERS:-"4"}


echo "Run django checks"
python manage.py check --deploy

echo "Migrating the database"
python manage.py migrate --noinput

echo "Running Django server on ${ADDRESS}:${PORT}"
gunicorn --bind "${ADDRESS}":"${PORT}" dashboard_service.wsgi:application --workers 2 --threads 4
