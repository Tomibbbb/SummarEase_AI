#!/bin/bash

# Start script for the SummarEase application
# This script provides options to start either the integrated app or separate services

set -e

# Default mode
MODE="integrated"

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --separate) MODE="separate"; shift ;;
        --integrated) MODE="integrated"; shift ;;
        --help) 
            echo "Usage: $0 [--integrated|--separate|--help]"
            echo ""
            echo "Options:"
            echo "  --integrated   Start the integrated application (default)"
            echo "  --separate     Start frontend and backend separately"
            echo "  --help         Show this help message"
            exit 0
            ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
done

# Ensure we're in the right directory
if [[ ! -d "frontend" || ! -d "backend" ]]; then
    echo "Error: This script must be run from the SummarEase project root directory"
    echo "Both 'frontend' and 'backend' directories must exist"
    exit 1
fi

# Start the selected mode
if [[ "$MODE" == "integrated" ]]; then
    echo "Starting SummarEase integrated application..."
    
    # Run setup script first
    bash ./setup_integrated.sh
    
    # Start with docker-compose if available
    if command -v docker-compose &> /dev/null; then
        echo "Using docker-compose for integrated mode..."
        docker-compose -f docker-compose.integrated.yml up
    else
        # Fallback to direct execution
        echo "Starting integrated app directly..."
        cd backend
        python3 integrated_app.py
    fi
else
    echo "Starting SummarEase with separate frontend and backend..."
    
    # Start with docker-compose if available
    if command -v docker-compose &> /dev/null; then
        echo "Using docker-compose for separate services..."
        docker-compose up
    else
        echo "Error: Docker Compose is required for separate mode."
        echo "Please install Docker Compose or use --integrated mode."
        exit 1
    fi
fi