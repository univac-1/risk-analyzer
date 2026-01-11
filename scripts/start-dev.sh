#!/bin/bash
# Start development servers

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting development servers...${NC}"

# Determine workspace path
WORKSPACE="${WORKSPACE:-/workspace}"
if [ ! -d "$WORKSPACE/backend" ]; then
    WORKSPACE="$(dirname "$(dirname "$(readlink -f "$0")")")"
fi

# Start backend in background
echo -e "${GREEN}Starting backend (FastAPI)...${NC}"
cd "$WORKSPACE/backend"
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start frontend in background
echo -e "${GREEN}Starting frontend (Vite)...${NC}"
cd "$WORKSPACE/frontend"
npm run dev -- --host 0.0.0.0 &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}Development servers started!${NC}"
echo "  Backend:  http://localhost:8000 (PID: $BACKEND_PID)"
echo "  Frontend: http://localhost:3000 (PID: $FRONTEND_PID)"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for both processes
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
