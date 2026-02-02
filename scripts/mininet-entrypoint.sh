#!/bin/bash
# Mininet Container Entrypoint

echo "Starting Mininet Container..."

# Start OVS
service openvswitch-switch start

# Check if ovs-vswitchd is running, if not start it
if ! pgrep -x "ovs-vswitchd" > /dev/null; then
    echo "Starting ovs-vswitchd..."
    ovs-vswitchd --pidfile --detach --log-file
fi

echo "Open vSwitch ready"
echo "ONOS Controller: $ONOS_IP:6653"

# Execute command
exec "$@"
