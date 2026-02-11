#!/bin/bash

echo "Adding missing enum values (outside transaction)..."
python -c "
import os, sys
url = os.getenv('DATABASE_URL', '')
if not url:
    print('DATABASE_URL not set, skipping enum patch')
    sys.exit(0)
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
    echo "Warning: Database migration failed. Starting server anyway..."
    echo "Please run migrations manually or check database connectivity."
fi

# 元のコマンドを実行
exec "$@"
