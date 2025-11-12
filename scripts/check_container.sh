#!/bin/bash

set -e

echo "Checking container security..."

# Build image
echo "Building Docker image..."
docker build -t secdev-app .

# Check image size
echo "Image size:"
docker images secdev-app

# Check layers
echo "Image layers:"
docker history secdev-app

echo "🔐 Checking non-root user..."
USER_ID=$(docker run --rm secdev-app id -u)
if [ "$USER_ID" != "0" ]; then
    echo "Running as non-root user (UID: $USER_ID)"
else
    echo "Running as root user!"
    exit 1
fi

# Test healthcheck
echo "Testing healthcheck..."
docker run -d --name test-container -p 8000:8000 secdev-app
sleep 10

# Wait for healthcheck to pass
timeout 60s bash -c 'until docker inspect test-container --format "{{.State.Health.Status}}" | grep -q "healthy"; do sleep 2; done' && echo "Healthcheck passed"

# Cleanup
docker stop test-container
docker rm test-container

echo "All container checks passed!"
