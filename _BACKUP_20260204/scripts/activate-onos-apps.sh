#!/bin/bash
# ONOS App Activation Script
# This script ensures required ONOS apps are active on container startup

echo "Waiting for ONOS to be ready..."
sleep 30

echo "Activating OpenFlow app..."
curl -u onos:rocks -X POST http://localhost:8181/onos/v1/applications/org.onosproject.openflow/active

echo "Activating Reactive Forwarding app..."
curl -u onos:rocks -X POST http://localhost:8181/onos/v1/applications/org.onosproject.fwd/active

echo "Activating ProxyARP app..."
curl -u onos:rocks -X POST http://localhost:8181/onos/v1/applications/org.onosproject.proxyarp/active

echo "Listing active applications..."
curl -u onos:rocks http://localhost:8181/onos/v1/applications | jq '.applications[] | select(.state=="ACTIVE") | .name'

echo "ONOS apps activated successfully!"
