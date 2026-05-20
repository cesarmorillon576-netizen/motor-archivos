#!/bin/bash

set -e

echo "--------Configuración de entorno--------"

echo "Dependencias de python..."
sudo apt update
sudo apt install python3-pip python3-dev libpq-dev -y

echo "Librerias necesarias para python..."
pip3 install -r requeriments.txt --break-system-packages

echo "Configuración completada exitosamente"


