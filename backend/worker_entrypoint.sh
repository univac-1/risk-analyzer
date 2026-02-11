#!/bin/bash

echo "Starting health check server..."
# Simple health check server on port 8080
python -c "
import http.server
import socketserver
import threading

class HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')
    def log_message(self, format, *args):
        pass  # Suppress logging

PORT = 8080
with socketserver.TCPServer(('', PORT), HealthHandler) as httpd:
    print(f'Health check server running on port {PORT}')
    httpd.serve_forever()
" &

echo "Adding missing enum values (outside transaction)..."
python -c "
import os, sys
url = os.getenv('DATABASE_URL', '')
if not url:
    print('DATABASE_URL not set, skipping enum patch')
    sys.exit(0)
# psycopg2 用に変換
url = url.replace('postgresql+asyncpg://', 'postgresql://')
try:
    from sqlalchemy import create_engine, text
    engine = create_engine(url, isolation_level='AUTOCOMMIT')
    with engine.connect() as conn:
        conn.execute(text(\"ALTER TYPE riskcategory ADD VALUE IF NOT EXISTS 'public_nuisance'\"))
    print('Enum patch applied successfully')
except Exception as e:
    print(f'Enum patch warning: {e}')
"

echo "Running database migrations..."
if alembic upgrade head; then
    echo "Migrations completed successfully."
else
    echo "Warning: Database migration failed. Starting worker anyway..."
fi

echo "Starting Celery worker..."
exec celery -A app.celery_app worker --loglevel=info --queues=default,analysis
