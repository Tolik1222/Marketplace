#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input

python manage.py migrate

export DJANGO_SUPERUSER_PASSWORD='doter222'
python manage.py createsuperuser --noinput --username doter222 --email admin@example.com || true