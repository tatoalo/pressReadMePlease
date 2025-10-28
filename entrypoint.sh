#!/bin/bash

# Run e2e startup test
echo "Running E2E startup test..."
python /src/e2e_startup.py

# Check if e2e test passed
if [ $? -ne 0 ]; then
    echo "E2E startup test failed! Container will still start, but please check the logs."
fi

# Start cron
cron -f
