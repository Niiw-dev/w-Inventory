#!/bin/bash
echo "BUILD START"

python3.9 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

python manage.py collectstatic --noinput --clear

echo "BUILD END"