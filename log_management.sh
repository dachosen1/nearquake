#!/bin/bash

# Define the directory containing the log files
LOG_DIR="/usr/src/app/logs"

# Delete files older than 30 days
find "$LOG_DIR" -name "*.log" -mtime +30 -exec rm {} \;

echo "Done. Removed logs older than 30 days"
