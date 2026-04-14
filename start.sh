#!/bin/bash
echo "Generating factsheet..."
python generate.py
echo "Starting server..."
exec gunicorn server:app --timeout 300 --workers 1
