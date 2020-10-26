#!/bin/bash
# echo "Collect static files"
# python manage.py collectstatic --noinput
echo "Generate database migrations"
python manage.py makemigrations
echo "Apply database migrations"
python manage.py migrate
echo "Starting server"
daphne FFXIV.asgi:application -b 0.0.0.0 -p 8002