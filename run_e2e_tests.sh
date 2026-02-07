#!/bin/bash

# E2E Testing Quick Start Script
# Runs the complete end-to-end test suite for the Witt-Classic prediction game

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        WITT-CLASSIC E2E TESTING QUICK START                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    echo -e "${YELLOW}Error: Please run this script from the project root directory${NC}"
    exit 1
fi

# Step 1: Seed test data
echo -e "\n${BLUE}Step 1: Seeding test data...${NC}"
if [ -f "worldcup.db" ]; then
    echo -e "${YELLOW}Removing existing database...${NC}"
    rm worldcup.db
fi
python3 scripts/seed_test_data.py

# Step 2: Wait for user to start backend
echo -e "\n${BLUE}Step 2: Backend setup${NC}"
echo "The backend needs to be running for tests. You can:"
echo "  Option A: Start backend in another terminal:"
echo "    python3 -m uvicorn app.main:app --port 8080"
echo "  Option B: Let this script start it (runs in background)"
echo ""
read -p "Start backend in background? (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}Starting backend...${NC}"
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080 > /tmp/backend.log 2>&1 &
    BACKEND_PID=$!
    echo "Backend started with PID: $BACKEND_PID"
    sleep 3

    # Check if backend started successfully
    if ! curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo -e "${YELLOW}Warning: Backend health check failed${NC}"
        echo "Check logs with: tail -f /tmp/backend.log"
    else
        echo -e "${GREEN}Backend is running${NC}"
    fi
fi

# Step 3: Run tests
echo -e "\n${BLUE}Step 3: Running E2E tests...${NC}"
echo "Running: pytest tests/test_e2e_scenarios.py -v"
echo ""

pytest tests/test_e2e_scenarios.py -v

# Check test result
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed!${NC}"
    TESTS_PASSED=true
else
    echo -e "\n${YELLOW}✗ Some tests failed${NC}"
    TESTS_PASSED=false
fi

# Step 4: Cleanup
echo -e "\n${BLUE}Step 4: Cleanup${NC}"
if [ ! -z "$BACKEND_PID" ]; then
    echo "Stopping backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null || true
    sleep 1
fi

# Summary
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                        TEST SUMMARY                           ║"
echo "╚════════════════════════════════════════════════════════════════╝"

if [ "$TESTS_PASSED" = true ]; then
    echo -e "\n${GREEN}✓ E2E Testing Complete - All Tests Passed!${NC}"
    echo -e "\nWhat was tested:"
    echo "  ✓ Scenario 1: Login and create league"
    echo "  ✓ Scenario 2: Login and join league"
    echo "  ✓ Scenario 3: Set predictions (multiple users)"
    echo "  ✓ Scenario 4: Admin update match results"
    echo "  ✓ Scenario 5: Witt's-classic scoring rules"
    echo "  ✓ Scenario 6: League standings updated"
    echo "  ✓ Bonus: Complete end-to-end workflow"
else
    echo -e "\n${YELLOW}✗ E2E Testing Failed - Check Errors Above${NC}"
fi

echo ""
echo "Next steps:"
echo "  1. Review test results above"
echo "  2. Check database: sqlite3 worldcup.db '.tables'"
echo "  3. View logs: tail -f /tmp/backend.log (if backend crashed)"
echo "  4. Manual testing: See E2E_TESTING_GUIDE.md"
echo ""
