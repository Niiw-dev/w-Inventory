#!/bin/bash
echo "BUILD START"

# Crear y activar entorno virtual
python3.9 -m venv venv
source venv/bin/activate

# Instalar dependencias dentro del venv
pip install -r requirements.txt

# Ejecutar collectstatic
python manage.py collectstatic --noinput --clear

echo "BUILD END"