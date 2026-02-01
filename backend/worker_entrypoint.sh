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

echo "Running database migrations..."
if alembic upgrade head; then
    echo "Migrations completed successfully."
else
    echo "Warning: Database migration failed. Starting worker anyway..."
fi

echo "Starting Celery worker..."
exec celery -A app.celery_app worker --loglevel=info
