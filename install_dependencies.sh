#!/bin/bash
# Script to install the required dependencies for the Toggl Worklog integration

echo "Installing dependencies for Toggl Worklog integration..."

# Install Python dependencies
pip3 install -r requirements.txt

echo "Dependencies installed successfully!"
echo ""
echo "To test the Toggl API functionality, run:"
echo "python3 tests/standalone_api_test.py --api-token YOUR_API_TOKEN --workspace-id YOUR_WORKSPACE_ID"
echo ""
echo "Replace YOUR_API_TOKEN and YOUR_WORKSPACE_ID with your actual values."
