#!/bin/bash
# Test GitHub Actions workflows locally using act
# Usage: ./test-workflow-locally.sh [job_name]

set -e

echo "🚀 GitHub Actions Local Testing"
echo "================================"
echo ""

# Check if act is installed
if ! command -v act &> /dev/null; then
    echo "❌ 'act' is not installed!"
    echo "Install it with: curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash"
    exit 1
fi

# Check if Docker is available
if ! docker ps &> /dev/null; then
    echo "⚠️  Docker is not available or not running"
    echo "Note: In dev containers, you may need to use the host Docker"
    echo "Continuing anyway..."
fi

echo "Available workflows and jobs:"
echo "----------------------------"
act -l
echo ""

if [ -z "$1" ]; then
    echo "Select what to test:"
    echo ""
    echo "1) Run just the Python version extraction job"
    echo "   Command: act -j get-python-version"
    echo ""
    echo "2) Run the full CI workflow (both jobs)"
    echo "   Command: act -W .github/workflows/ci.yml"
    echo ""
    echo "3) Run just the CI tests job (will use cached Python version)"
    echo "   Command: act -j ci"
    echo ""
    echo "4) Run a specific job by name"
    echo "   Command: ./test-workflow-locally.sh <job-name>"
    echo ""
    echo "Options:"
    echo "  -n  Dry run (show what would be executed)"
    echo "  -v  Verbose output"
    echo "  --list  List all workflows"
    echo ""
    exit 0
fi

JOB_NAME="$1"

echo "🔧 Running job: $JOB_NAME"
echo ""

# Run the specific job
act -j "$JOB_NAME" --verbose
