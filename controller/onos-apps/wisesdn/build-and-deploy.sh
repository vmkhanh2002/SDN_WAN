#!/bin/bash
# Build and Deploy SDN-WISE ONOS Application

set -e

echo "================================"
echo "SDN-WISE ONOS App - Build & Deploy"
echo "================================"

# Navigate to project directory
cd "$(dirname "$0")"
PROJECT_DIR=$(pwd)

echo "=> Project directory: $PROJECT_DIR"

# Check if Maven is available
if ! command -v mvn &> /dev/null; then
    echo "ERROR: Maven not found. Please install Maven."
    exit 1
fi

echo "=> Building with Maven..."
mvn clean install

if [ $? -ne 0 ]; then
    echo "ERROR: Build failed!"
    exit 1
fi

echo "SUCCESS: Build successful!"
echo ""

# Check if .oar file was created
OAR_FILE="target/wisesdn-1.0-SNAPSHOT.oar"
if [ ! -f "$OAR_FILE" ]; then
    echo "ERROR: .oar file not found!"
    exit 1
fi

echo "=> Found: $OAR_FILE"
echo ""

# Deploy to ONOS
echo "=> Deploying to ONOS..."

ONOS_URL="${ONOS_URL:-http://172.25.0.2:8181}"
ONOS_USER="${ONOS_USER:-onos}"
ONOS_PASS="${ONOS_PASS:-rocks}"

echo "   ONOS URL: $ONOS_URL"

# Install application
curl -u $ONOS_USER:$ONOS_PASS \
     -X POST \
     -F "file=@$OAR_FILE" \
     "$ONOS_URL/onos/v1/applications?activate=true"

echo ""
echo "SUCCESS: Deployment complete!"
echo ""

# Verify installation
echo "=> Verifying installation..."
sleep 2

APP_STATUS=$(curl -s -u $ONOS_USER:$ONOS_PASS \
    "$ONOS_URL/onos/v1/applications/org.onosproject.wisesdn" | \
    grep -o '"state":"[^"]*"' | cut -d'"' -f4)

if [ "$APP_STATUS" == "ACTIVE" ]; then
    echo "SUCCESS: Application is ACTIVE"
else
    echo "WARNING: Application status: $APP_STATUS"
fi

echo ""
echo "================================"
echo "SDN-WISE App Ready!"
echo "================================"
echo ""
echo "Test endpoints:"
echo "  curl -u onos:rocks $ONOS_URL/onos/wisesdn/api/devices"
echo "  curl -u onos:rocks $ONOS_URL/onos/wisesdn/api/topology"
echo ""
