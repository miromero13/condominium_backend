#!/bin/bash

# Salir si hay algún error
set -e

echo "📦 Instalando dependencias..."
pip install -r requirements.txt

echo "🗄️ Aplicando migraciones..."
python manage.py migrate --noinput

echo "🧹 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "🚀 Iniciando Gunicorn..."
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
