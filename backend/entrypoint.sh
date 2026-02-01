#!/bin/bash

echo "Running database migrations..."
if alembic upgrade head; then
    echo "Migrations completed successfully."
else
    echo "Warning: Database migration failed. Starting server anyway..."
    echo "Please run migrations manually or check database connectivity."
fi

# 元のコマンドを実行
exec "$@"
