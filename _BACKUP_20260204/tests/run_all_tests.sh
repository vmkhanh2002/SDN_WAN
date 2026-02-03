#!/bin/bash
# Run all tests and generate comprehensive report

set -e

echo "========================================"
echo "SDN-WISE Production Test Suite"
echo "========================================"
echo ""

# Navigate to project directory
cd "$(dirname "$0")/.."

# Run functional tests
echo "[1/3] Running Functional Tests..."
python3 tests/test_suite.py

# Run hardware readiness tests
echo ""
echo "[2/3] Running Hardware Readiness Tests..."
python3 tests/hardware_readiness.py

# Run container verification
echo ""
echo "[3/3] Running Container Verification..."
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "========================================"
echo "All tests completed!"
echo "Check test_report.html for detailed results"
echo "========================================"
