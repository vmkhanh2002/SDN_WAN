#!/bin/bash

echo ""
echo "Workspace: /workspace"
echo "ONOS Controller: $ONOS_IP:6653"
echo ""

# List available examples
if [ -d "/workspace" ]; then
    echo "Applications in workspace:"
    ls -la /workspace/*.c 2>/dev/null || echo "   (none yet)"
fi

echo ""
echo "=========================================="
echo "Ready! Use 'docker exec -it cooja-simulator bash'"
echo "=========================================="

# Execute command
exec "$@"
