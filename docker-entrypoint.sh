#!/bin/bash

echo "Checking database connection"
until python manage.py check --database default; do
  echo "Database is unavailable - sleeping"
  sleep 1
done
echo "Database is up - executing command"

# echo "Collect static files"
# python manage.py collectstatic --noinput

echo "Generate database migrations"
python manage.py makemigrations

echo "Apply database migrations"
python manage.py migrate

echo "Starting server"
daphne FFXIV.asgi:application -b 0.0.0.0 -p 8002
