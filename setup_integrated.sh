#!/bin/bash

# Setup script for integrated SummarEase frontend and backend

echo "Setting up integrated SummarEase application..."

# Ensure the script is run from the right directory
if [[ ! -d "frontend" || ! -d "backend" ]]; then
    echo "Error: This script must be run from the SummarEase project root directory"
    echo "Both 'frontend' and 'backend' directories must exist"
    exit 1
fi

# Create uploads directory for file storage
echo "Setting up uploads directory..."
mkdir -p uploads

# Set correct permissions
echo "Setting correct permissions..."
chmod -R 755 uploads

# Create minimal static directory structure in backend
echo "Creating minimal static directory for backend..."
mkdir -p backend/static

echo "Setup complete! You can now run the integrated application using docker-compose:"
echo "docker-compose -f docker-compose.integrated.yml up -d"
echo ""
echo "Or run it directly with:"
echo "cd backend && python integrated_app.py"
echo ""
echo "Then visit: http://localhost:8000"