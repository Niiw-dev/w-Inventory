#!/bin/bash

# Salir inmediatamente si ocurre un error
set -e

echo "Instalando dependencias..."
python3 -m pip install -r requirements.txt

echo "Recolectando archivos estáticos..."
python3 manage.py collectstatic --noinput --clear

echo "Build finalizado con éxito."