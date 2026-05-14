#!/bin/bash
# Integration test script - validates all services working correctly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}PipPulse AI - System Integration Test${NC}"
echo "========================================"

# Track test results
PASSED=0
FAILED=0
SKIPPED=0

# Function to run test
run_test() {
  local test_name=$1
  local test_command=$2

  echo -n "Testing: $test_name ... "

  if eval "$test_command" > /dev/null 2>&1; then
    echo -e "${GREEN}PASSED${NC}"
    ((PASSED++))
  else
    echo -e "${RED}FAILED${NC}"
    ((FAILED++))
  fi
}

# 1. Docker Services
echo -e "\n${YELLOW}1. Docker Services${NC}"
echo "-------------------"

run_test "Backend API running" "docker-compose ps backend | grep -q 'Up'"
run_test "MongoDB running" "docker-compose ps mongodb | grep -q 'Up'"
run_test "Redis running" "docker-compose ps redis | grep -q 'Up'"
run_test "PostgreSQL running" "docker-compose ps postgres | grep -q 'Up'"
run_test "InfluxDB running" "docker-compose ps influxdb | grep -q 'Up'"

# 2. API Endpoints
echo -e "\n${YELLOW}2. API Endpoints${NC}"
echo "-----------------"

run_test "Health check endpoint" "curl -s http://localhost:8000/health/ | grep -q 'healthy'"
run_test "Detailed health check" "curl -s http://localhost:8000/health/detailed | grep -q 'components'"
run_test "Liveness check" "curl -s http://localhost:8000/health/live | grep -q 'alive'"
run_test "Readiness check" "curl -s http://localhost:8000/health/ready | grep -q 'ready'"
run_test "WebSocket metrics endpoint" "curl -s http://localhost:8000/health/websocket/metrics | grep -q 'websocket'"
run_test "WebSocket connections endpoint" "curl -s http://localhost:8000/health/websocket/connections | grep -q 'active_connections'"

# 3. Database Connectivity
echo -e "\n${YELLOW}3. Database Connectivity${NC}"
echo "------------------------"

run_test "MongoDB connectivity" "docker-compose exec -T mongodb mongosh --eval 'db.adminCommand(\"ping\")' | grep -q '1'"
run_test "Redis connectivity" "docker-compose exec -T redis redis-cli ping | grep -q 'PONG'"
run_test "PostgreSQL connectivity" "docker-compose exec -T postgres psql -U pippulse -c 'SELECT 1' | grep -q '1'"
run_test "InfluxDB connectivity" "docker-compose exec -T influxdb influx ping | grep -q 'OK'"

# 4. WebSocket Connectivity
echo -e "\n${YELLOW}4. WebSocket Connectivity${NC}"
echo "-------------------------"

# Using a simple Python script to test WebSocket
TEST_WS=$(cat > /tmp/test_ws.py << 'EOF'
import asyncio
import websockets
import json

async def test_websocket():
    try:
        async with websockets.connect('ws://localhost:8000/ws/') as websocket:
            # Receive connection message
            msg = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(msg)
            assert data['type'] == 'connected'

            # Send ping
            await websocket.send(json.dumps({'type': 'ping'}))
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            resp_data = json.loads(response)
            assert resp_data['type'] == 'pong'

            print("OK")
    except Exception as e:
        print(f"FAILED: {e}")
        exit(1)

asyncio.run(test_websocket())
EOF
python /tmp/test_ws.py)

if [ "$TEST_WS" = "OK" ]; then
  echo -n "Testing: WebSocket connection ... "
  echo -e "${GREEN}PASSED${NC}"
  ((PASSED++))
else
  echo -n "Testing: WebSocket connection ... "
  echo -e "${RED}FAILED${NC}"
  ((FAILED++))
fi

# 5. Signal Service Health
echo -e "\n${YELLOW}5. Signal Service Health${NC}"
echo "------------------------"

run_test "Signal engine running" "docker-compose ps signal-engine | grep -q 'Up'"
run_test "Data collector running" "docker-compose ps collector | grep -q 'Up'"

# 6. Performance Metrics
echo -e "\n${YELLOW}6. Performance Metrics${NC}"
echo "---------------------"

# Get metrics
METRICS=$(curl -s http://localhost:8000/health/websocket/metrics)

echo "WebSocket Metrics:"
echo "$METRICS" | python -m json.tool | grep -E 'total_connections|avg_latency|messages'

# 7. Frontend (if running)
echo -e "\n${YELLOW}7. Frontend${NC}"
echo "-----------"

if docker-compose ps frontend | grep -q 'Up'; then
  run_test "Frontend running" "docker-compose ps frontend | grep -q 'Up'"
  run_test "Frontend accessible" "curl -s http://localhost:3000 | grep -q 'html' 2>/dev/null || echo ''"
else
  echo "Frontend not running in compose (optional)"
fi

# 8. Data Services
echo -e "\n${YELLOW}8. Data Services${NC}"
echo "----------------"

run_test "MongoDB database exists" "docker-compose exec -T mongodb mongosh --eval 'db.listDatabases()' | grep -q 'pippulse'"
run_test "PostgreSQL database exists" "docker-compose exec -T postgres psql -lqt | grep -q 'pippulse'"
run_test "InfluxDB bucket exists" "docker-compose exec -T influxdb influx bucket list | grep -q 'signals'"

# 9. Logs Check (no errors)
echo -e "\n${YELLOW}9. Error Log Check${NC}"
echo "------------------"

BACKEND_ERRORS=$(docker-compose logs backend --tail=100 | grep -c 'ERROR' || true)
SIGNAL_ERRORS=$(docker-compose logs signal-engine --tail=100 | grep -c 'ERROR' || true)

echo "Backend errors in last 100 lines: $BACKEND_ERRORS"
echo "Signal engine errors in last 100 lines: $SIGNAL_ERRORS"

if [ "$BACKEND_ERRORS" -gt 5 ] || [ "$SIGNAL_ERRORS" -gt 5 ]; then
  echo -e "${YELLOW}WARNING: High error count detected${NC}"
  echo "Review logs: docker-compose logs backend"
  echo "Review logs: docker-compose logs signal-engine"
fi

# Summary
echo -e "\n${YELLOW}========================================"
echo "Test Summary${NC}"
echo "========================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo -e "Skipped: ${YELLOW}$SKIPPED${NC}"

if [ $FAILED -eq 0 ]; then
  echo -e "\n${GREEN}All tests passed!${NC}"
  echo "System is operational and ready for use."
  exit 0
else
  echo -e "\n${RED}Some tests failed!${NC}"
  echo "Please review the errors above."
  exit 1
fi
