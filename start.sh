#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null || true
export FLASK_APP=app.py
export FLASK_ENV=production
python app.py --host=0.0.0.0 --port=5000
