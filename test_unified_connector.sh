#!/bin/bash
# Test script for Unified Connector

set -e  # Exit on error

echo "======================================================================"
echo "Unified Connector - Testing Script"
echo "======================================================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then
  echo -e "${RED}ERROR: Do not run as root!${NC}"
  exit 1
fi

# Function to print status
print_status() {
  echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
  echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
  echo -e "${RED}✗${NC} $1"
}

# Check prerequisites
echo ""
echo "Checking prerequisites..."

# Check Docker
if command -v docker &> /dev/null; then
  print_status "Docker installed"
else
  print_error "Docker not found. Please install Docker."
  exit 1
fi

# Check Colima (optional)
if command -v colima &> /dev/null; then
  print_status "Colima installed"

  # Check if Colima is running
  if colima status &> /dev/null; then
    print_status "Colima is running"
  else
    print_warning "Colima is not running. Starting..."
    colima start
  fi
else
  print_warning "Colima not found. Using default Docker."
fi

# Check docker-compose
if command -v docker-compose &> /dev/null; then
  print_status "docker-compose installed"
else
  print_error "docker-compose not found. Please install docker-compose."
  exit 1
fi

# Test 1: Build images
echo ""
echo "======================================================================"
echo "Test 1: Building Docker images"
echo "======================================================================"

docker-compose -f docker-compose.unified.yml build
print_status "Images built successfully"

# Test 2: Start OT Simulator
echo ""
echo "======================================================================"
echo "Test 2: Starting OT Simulator"
echo "======================================================================"

docker-compose -f docker-compose.unified.yml up -d ot_simulator
sleep 5

# Check if OT Simulator is running
if curl -f http://localhost:8989/health &> /dev/null; then
  print_status "OT Simulator is running"
else
  print_error "OT Simulator health check failed"
  docker-compose -f docker-compose.unified.yml logs ot_simulator
  exit 1
fi

# Test 3: Start Unified Connector
echo ""
echo "======================================================================"
echo "Test 3: Starting Unified Connector"
echo "======================================================================"

# Set environment variables
export CONNECTOR_MASTER_PASSWORD="test-password-$(date +%s)"

docker-compose -f docker-compose.unified.yml up -d unified_connector
sleep 10

# Check if Unified Connector is running
if curl -f http://localhost:8081/health &> /dev/null; then
  print_status "Unified Connector is running"
else
  print_error "Unified Connector health check failed"
  docker-compose -f docker-compose.unified.yml logs unified_connector
  exit 1
fi

# Test 4: Protocol Discovery
echo ""
echo "======================================================================"
echo "Test 4: Testing Protocol Discovery"
echo "======================================================================"

# Trigger discovery scan
echo "Triggering discovery scan..."
curl -X POST http://localhost:8080/api/discovery/scan
sleep 5

# Get discovered servers
echo ""
echo "Discovered servers:"
curl -s http://localhost:8080/api/discovery/servers | python3 -m json.tool

# Test 5: Check Metrics
echo ""
echo "======================================================================"
echo "Test 5: Checking Metrics"
echo "======================================================================"

curl -s http://localhost:8080/api/metrics | python3 -m json.tool

# Test 6: Check Status
echo ""
echo "======================================================================"
echo "Test 6: Checking Status"
echo "======================================================================"

curl -s http://localhost:8080/api/status | python3 -m json.tool

# Test 7: View Logs
echo ""
echo "======================================================================"
echo "Test 7: Recent Logs"
echo "======================================================================"

echo ""
echo "OT Simulator logs:"
docker-compose -f docker-compose.unified.yml logs --tail=20 ot_simulator

echo ""
echo "Unified Connector logs:"
docker-compose -f docker-compose.unified.yml logs --tail=20 unified_connector

# Summary
echo ""
echo "======================================================================"
echo "Test Summary"
echo "======================================================================"
print_status "All tests passed!"
echo ""
echo "Services running:"
echo "  - OT Simulator:      http://localhost:8989"
echo "  - Unified Connector: http://localhost:8080"
echo "  - Health Check:      http://localhost:8081/health"
echo "  - Prometheus:        http://localhost:9090/metrics"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose.unified.yml logs -f"
echo ""
echo "To stop services:"
echo "  docker-compose -f docker-compose.unified.yml down"
echo ""
echo "======================================================================"
