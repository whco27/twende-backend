#!/bin/bash

# Twende Tours - Frontend Deployment Script
# This script builds and deploys frontend assets to the backend's public directory
# 
# Usage:
#   ./scripts/deploy_frontend.sh [path/to/frontend/repo]
#
# If no path is provided, it looks for ../twende-frontend or ../frontend

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory (where this script is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
PUBLIC_DIR="$BACKEND_DIR/public"

echo -e "${GREEN}=== Twende Tours Frontend Deployment ===${NC}"
echo ""

# Find frontend directory
if [ -n "$1" ]; then
    FRONTEND_DIR="$1"
elif [ -d "$BACKEND_DIR/../twende-frontend" ]; then
    FRONTEND_DIR="$BACKEND_DIR/../twende-frontend"
elif [ -d "$BACKEND_DIR/../frontend" ]; then
    FRONTEND_DIR="$BACKEND_DIR/../frontend"
else
    echo -e "${RED}Error: Frontend directory not found${NC}"
    echo "Please provide the path to the frontend repository:"
    echo "  $0 /path/to/frontend"
    echo ""
    echo "Or place the frontend repository in one of these locations:"
    echo "  - ../twende-frontend"
    echo "  - ../frontend"
    exit 1
fi

# Verify frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}Error: Frontend directory not found at: $FRONTEND_DIR${NC}"
    exit 1
fi

echo -e "Frontend directory: ${YELLOW}$FRONTEND_DIR${NC}"
echo -e "Backend directory:  ${YELLOW}$BACKEND_DIR${NC}"
echo -e "Public directory:   ${YELLOW}$PUBLIC_DIR${NC}"
echo ""

# Check if package.json exists
if [ ! -f "$FRONTEND_DIR/package.json" ]; then
    echo -e "${RED}Error: No package.json found in frontend directory${NC}"
    exit 1
fi

# Navigate to frontend directory
cd "$FRONTEND_DIR"

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    npm install
fi

# Build the frontend
echo -e "${YELLOW}Building frontend...${NC}"
npm run build

# Determine build output directory (dist for Vite, build for CRA)
if [ -d "dist" ]; then
    BUILD_DIR="dist"
elif [ -d "build" ]; then
    BUILD_DIR="build"
else
    echo -e "${RED}Error: Build directory not found (expected 'dist' or 'build')${NC}"
    exit 1
fi

echo -e "Build output: ${YELLOW}$FRONTEND_DIR/$BUILD_DIR${NC}"

# Clear public directory (except .gitkeep)
echo -e "${YELLOW}Clearing old frontend files from public directory...${NC}"
find "$PUBLIC_DIR" -mindepth 1 ! -name '.gitkeep' -delete 2>/dev/null || true

# Copy build files to public directory
echo -e "${YELLOW}Copying build files to backend public directory...${NC}"
cp -r "$FRONTEND_DIR/$BUILD_DIR/"* "$PUBLIC_DIR/"

# Verify deployment
if [ -f "$PUBLIC_DIR/index.html" ]; then
    echo ""
    echo -e "${GREEN}=== Deployment Complete ===${NC}"
    echo ""
    echo "Frontend assets deployed to: $PUBLIC_DIR"
    echo ""
    echo "Files deployed:"
    ls -la "$PUBLIC_DIR" | head -20
    echo ""
    echo -e "${GREEN}Next steps:${NC}"
    echo "1. Set ENABLE_CORS=false in your .env file (optional for same-origin)"
    echo "2. Start the backend: python app.py"
    echo "3. Access the app at http://localhost:5000"
else
    echo -e "${RED}Error: Deployment verification failed - index.html not found${NC}"
    exit 1
fi
