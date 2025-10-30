#!/bin/bash
set -e

# JSON data configuration
JSON_PATH="${DATA_PATH:-/app/data}/fianzas_wfs_layer.json"
REFRESH_DAYS="${DATA_REFRESH_DAYS:-30}"
ENVIRONMENT="${ENVIRONMENT:-pro}"

echo "========================================"
echo "AOD Fianzas Backend - Starting"
echo "========================================"
echo "Environment: $ENVIRONMENT"
echo "Data path: $JSON_PATH"
echo "Refresh interval: $REFRESH_DAYS days"
echo ""

should_refresh=false

# Check if JSON file exists
if [ ! -f "$JSON_PATH" ]; then
    echo "JSON data file not found at $JSON_PATH"
    should_refresh=true
else
    # Calculate file age in days
    file_timestamp=$(stat -c %Y "$JSON_PATH" 2>/dev/null || stat -f %m "$JSON_PATH" 2>/dev/null)
    current_timestamp=$(date +%s)
    file_age_seconds=$((current_timestamp - file_timestamp))
    file_age_days=$((file_age_seconds / 86400))

    echo "JSON data file found (age: $file_age_days days)"

    if [ $file_age_days -ge $REFRESH_DAYS ]; then
        echo "Data is older than $REFRESH_DAYS days, refresh needed"
        should_refresh=true
    else
        echo "Data is fresh, no refresh needed"
    fi
fi

# Handle refresh if needed
if [ "$should_refresh" = true ]; then
    if [ "$ENVIRONMENT" = "local" ]; then
        echo ""
        echo "ERROR: JSON file missing in local environment"
        echo "Please run fetch_fianzas_layer.py manually:"
        echo "  cd aod-fianzas-back"
        echo "  uv run python fetch_fianzas_layer.py --output data/fianzas_wfs_layer.json"
        echo ""
        exit 1
    fi

    echo "Attempting to download fresh data..."

    # Create data directory if it doesn't exist
    mkdir -p "$(dirname "$JSON_PATH")"

    # Attempt download
    if python fetch_fianzas_layer.py --output "$JSON_PATH"; then
        echo "Successfully downloaded fresh data"
    else
        echo ""
        echo "WARNING: Failed to download data"
        if [ ! -f "$JSON_PATH" ]; then
            echo "WARNING: No existing data available, starting with empty dataset"
        else
            echo "WARNING: Continuing with existing data"
        fi
        echo ""
    fi
fi

echo ""
echo "Starting FastAPI application..."
echo "========================================"
echo ""

# Start the application
exec uvicorn main:app --host 0.0.0.0 --port 8000 --root-path /servicios/alquileres-api
