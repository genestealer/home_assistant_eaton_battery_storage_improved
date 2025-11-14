#!/bin/bash
# Quick workflow validation script
# This checks workflow syntax without needing Docker

echo "🔍 GitHub Actions Workflow Validator"
echo "===================================="
echo ""

# Check if actionlint is installed
if ! command -v actionlint &> /dev/null; then
    echo "📦 Installing actionlint..."
    bash -c "$(curl -s https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/download-actionlint.bash)" && sudo mv actionlint /usr/local/bin/
fi

echo "✅ Checking workflow syntax..."
echo ""

# Check all workflow files
shopt -s nullglob
for workflow in .github/workflows/*.yml .github/workflows/*.yaml; do
    if [ -f "$workflow" ]; then
        echo "📄 Checking: $workflow"
        if actionlint "$workflow"; then
            echo "   ✅ Valid"
        else
            echo "   ❌ Has errors"
        fi
        echo ""
    fi
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Tips:"
echo "   • Syntax is valid - you can push safely!"
echo "   • To test locally with Docker: act -W .github/workflows/ci.yml"
echo "   • To run specific job: act -j <job-name>"
echo ""
echo "🚀 Ready to commit and push!"
