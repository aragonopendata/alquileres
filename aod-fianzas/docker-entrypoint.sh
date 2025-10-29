#!/bin/sh
# Frontend Docker Entrypoint Script
# Selects the appropriate config.json based on ENVIRONMENT variable

set -e

# Configuration directory inside container
CONFIG_DIR="/usr/share/nginx/html/servicios/alquileres/assets/config"

# Default to pro (production) if ENVIRONMENT not set
ENVIRONMENT=${ENVIRONMENT:-pro}

echo "=========================================="
echo "AOD Fianzas Frontend - Starting"
echo "=========================================="
echo "Environment: $ENVIRONMENT"
echo "Config directory: $CONFIG_DIR"
echo ""

# Check which config files are available
echo "Available config files:"
ls -lh "$CONFIG_DIR"
echo ""

# Select and copy the appropriate config file based on ENVIRONMENT
case "$ENVIRONMENT" in
  local)
    echo "Using local Docker configuration"
    # Create config for Docker Compose local deployment (container networking)
    cat > "$CONFIG_DIR/config.json" <<EOF
{
  "apiUrl": "http://aod-fianzas-back:8000",
  "environment": "local",
  "igearServices": {
    "typedSearchUrl": "https://idearagon.aragon.es/servicios/TypedSearchService",
    "spatialSearchUrl": "https://idearagon.aragon.es/servicios/SpatialSearchService",
    "sitaWmsUrl": "https://idearagon.aragon.es/servicios/SITA_WMS",
    "visor2dUrl": "https://idearagon.aragon.es/datos/catalogo2/servlet/VisorServlet2D"
  }
}
EOF
    echo "Generated config.json with container networking (backend: aod-fianzas-back:8000)"
    ;;
  des)
    echo "Using desarrollo configuration (config.des.json)"
    if [ -f "$CONFIG_DIR/config.des.json" ]; then
      cp "$CONFIG_DIR/config.des.json" "$CONFIG_DIR/config.json"
      echo "Copied config.des.json to config.json"
    else
      echo "ERROR: config.des.json not found!"
      exit 1
    fi
    ;;
  pre)
    echo "Using preproduction configuration (config.pre.json)"
    if [ -f "$CONFIG_DIR/config.pre.json" ]; then
      cp "$CONFIG_DIR/config.pre.json" "$CONFIG_DIR/config.json"
      echo "Copied config.pre.json to config.json"
    else
      echo "ERROR: config.pre.json not found!"
      exit 1
    fi
    ;;
  pro)
    echo "Using production configuration (config.pro.json)"
    if [ -f "$CONFIG_DIR/config.pro.json" ]; then
      cp "$CONFIG_DIR/config.pro.json" "$CONFIG_DIR/config.json"
      echo "Copied config.pro.json to config.json"
    else
      echo "ERROR: config.pro.json not found!"
      exit 1
    fi
    ;;
  *)
    echo "WARNING: Unknown ENVIRONMENT '$ENVIRONMENT', defaulting to production"
    if [ -f "$CONFIG_DIR/config.pro.json" ]; then
      cp "$CONFIG_DIR/config.pro.json" "$CONFIG_DIR/config.json"
      echo "Copied config.pro.json to config.json"
    fi
    ;;
esac

echo ""
echo "Active configuration:"
cat "$CONFIG_DIR/config.json"
echo ""
echo "=========================================="
echo "Starting nginx..."
echo "=========================================="

# Start nginx in foreground
exec nginx -g 'daemon off;'
