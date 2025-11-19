#!/bin/bash
#
# Automation script to create manual tests for a new version.
#
# Usage: ./create_version_tests.sh <version> <features>
#
# Example: ./create_version_tests.sh v0.2.12 "cli,formatting,validation"
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

# Functions
print_error() {
    echo -e "${RED}✗ Error: $1${NC}" >&2
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check arguments
if [ $# -lt 2 ]; then
    print_error "Missing arguments"
    echo "Usage: $0 <version> <features>"
    echo ""
    echo "Arguments:"
    echo "  version   - Version number (e.g., v0.2.12)"
    echo "  features  - Comma-separated feature tags (e.g., \"cli,formatting,validation\")"
    echo ""
    echo "Example:"
    echo "  $0 v0.2.12 \"cli,formatting\""
    exit 1
fi

VERSION="$1"
FEATURES="$2"
DATE=$(date +%Y-%m-%d)

# Validate version format
if [[ ! "$VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    print_error "Invalid version format: $VERSION"
    echo "Expected format: vX.Y.Z (e.g., v0.2.12)"
    exit 1
fi

# Extract major.minor for directory structure
MAJOR_MINOR=$(echo "$VERSION" | sed -E 's/^(v[0-9]+\.[0-9]+)\.[0-9]+$/\1/')

print_info "Creating manual tests for $VERSION"
print_info "Features: $FEATURES"
print_info "Date: $DATE"
print_info "Major.Minor: $MAJOR_MINOR"
echo ""

# Create directories
TEST_DIR="${PROJECT_ROOT}/scripts/manual_tests/version/${VERSION}"
DOCS_DIR="${PROJECT_ROOT}/docs/development/process/testing/manual/${MAJOR_MINOR}"

if [ -d "$TEST_DIR" ]; then
    print_error "Version directory already exists: $TEST_DIR"
    exit 1
fi

print_info "Creating directories..."
mkdir -p "$TEST_DIR"
mkdir -p "$DOCS_DIR"

# Process template files
TEMPLATE_DIR="${SCRIPT_DIR}/version_test_template"

# Copy and process README.template.md
print_info "Creating version README..."
README_FILE="${TEST_DIR}/README.md"
cp "${TEMPLATE_DIR}/README.template.md" "$README_FILE"

# Build feature list
FEATURE_LIST=""
FEATURE_TEST_FILES=""
FEATURE_MARKERS=""

IFS=',' read -ra FEATURE_ARRAY <<< "$FEATURES"
for feature in "${FEATURE_ARRAY[@]}"; do
    feature=$(echo "$feature" | xargs) # Trim whitespace

    # Feature list
    FEATURE_LIST="${FEATURE_LIST}- **${feature}** - Feature description\n"

    # Feature test files
    FEATURE_TEST_FILES="${FEATURE_TEST_FILES}- \`${feature}_test.py\` - ${feature} feature tests\n"

    # Feature markers
    FEATURE_MARKERS="${FEATURE_MARKERS}- \`@pytest.mark.feature(\"${feature}\")\` - ${feature} tests\n"
done

# Replace placeholders in README
sed -i.bak "s|{VERSION}|${VERSION}|g" "$README_FILE"
sed -i.bak "s|{STATUS}|📅 PLANNED|g" "$README_FILE"
sed -i.bak "s|{FEATURES}|${FEATURES}|g" "$README_FILE"
sed -i.bak "s|{DATE}|${DATE}|g" "$README_FILE"
sed -i.bak "s|{FEATURE_LIST}|${FEATURE_LIST}|g" "$README_FILE"
sed -i.bak "s|{FEATURE_TEST_FILES}|${FEATURE_TEST_FILES}|g" "$README_FILE"
sed -i.bak "s|{FEATURE_TAG}|${FEATURE_ARRAY[0]}|g" "$README_FILE"
sed -i.bak "s|{FEATURE_MARKERS}|${FEATURE_MARKERS}|g" "$README_FILE"
sed -i.bak "s|{ROADMAP_LINK}|../../../docs/development/roadmap/version/${MAJOR_MINOR}/${VERSION}/|g" "$README_FILE"
sed -i.bak "s|{IMPLEMENTATION_LINK}|../../../docs/development/implementation/version/${MAJOR_MINOR}/${VERSION}.md|g" "$README_FILE"
sed -i.bak "s|{MANUAL_TEST_PLAN_LINK}|../../../docs/development/process/testing/manual/${MAJOR_MINOR}/${VERSION}-manual-tests.md|g" "$README_FILE"
rm "${README_FILE}.bak"

print_success "Created ${TEST_DIR}/README.md"

# Copy and process smoke_test.py
print_info "Creating smoke test..."
SMOKE_TEST="${TEST_DIR}/smoke_test.py"
cp "${TEMPLATE_DIR}/smoke_test.template.py" "$SMOKE_TEST"
sed -i.bak "s|{VERSION}|${VERSION}|g" "$SMOKE_TEST"
rm "${SMOKE_TEST}.bak"

print_success "Created ${TEST_DIR}/smoke_test.py"

# Create feature-specific test files
for feature in "${FEATURE_ARRAY[@]}"; do
    feature=$(echo "$feature" | xargs)

    print_info "Creating ${feature} test..."
    FEATURE_TEST="${TEST_DIR}/${feature}_test.py"
    cp "${TEMPLATE_DIR}/feature_test.template.py" "$FEATURE_TEST"

    # Capitalise feature name for display
    FEATURE_NAME=$(echo "$feature" | sed 's/_/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) tolower(substr($i,2))}1')

    sed -i.bak "s|{VERSION}|${VERSION}|g" "$FEATURE_TEST"
    sed -i.bak "s|{FEATURE_NAME}|${FEATURE_NAME}|g" "$FEATURE_TEST"
    sed -i.bak "s|{FEATURE_TAG}|${feature}|g" "$FEATURE_TEST"
    rm "${FEATURE_TEST}.bak"

    print_success "Created ${TEST_DIR}/${feature}_test.py"
done

# Create documentation test plan
print_info "Creating manual test plan documentation..."
DOC_TEMPLATE="${SCRIPT_DIR}/docs_template/manual-test-plan.template.md"
DOC_FILE="${DOCS_DIR}/${VERSION}-manual-tests.md"

# Check if template exists, if not create a basic one
if [ ! -f "$DOC_TEMPLATE" ]; then
    cat > "$DOC_FILE" << EOF
# ${VERSION} Manual Test Plan

**Status:** 📅 PLANNED
**Date Created:** ${DATE}
**Features:** ${FEATURES}

---

## Overview

Manual test plan for ragged ${VERSION}.

---

## Features Tested

${FEATURE_LIST}

---

## Test Scenarios

### Scenario 1: [Feature Name]

**Steps:**
1. Step 1
2. Step 2
3. Step 3

**Expected Results:**
- Result 1
- Result 2

**Actual Results:** [Fill in during testing]

---

## Verification Checklist

- [ ] All features work as expected
- [ ] Error messages are clear
- [ ] Performance is acceptable
- [ ] Documentation is accurate

---

## Executable Tests

Run automated tests:
\`\`\`bash
pytest scripts/manual_tests/version/${VERSION}/
\`\`\`

---

## Related Documentation

- [Roadmap](../../../roadmap/version/${MAJOR_MINOR}/${VERSION}/)
- [Implementation](../../../implementation/version/${MAJOR_MINOR}/${VERSION}.md)
- [Test Scripts](../../../../../scripts/manual_tests/version/${VERSION}/)

---

**Maintained By:** ragged development team
EOF
else
    cp "$DOC_TEMPLATE" "$DOC_FILE"
    sed -i.bak "s|{VERSION}|${VERSION}|g" "$DOC_FILE"
    sed -i.bak "s|{DATE}|${DATE}|g" "$DOC_FILE"
    sed -i.bak "s|{FEATURES}|${FEATURES}|g" "$DOC_FILE"
    sed -i.bak "s|{FEATURE_LIST}|${FEATURE_LIST}|g" "$DOC_FILE"
    sed -i.bak "s|{TEST_SCRIPTS_PATH}|scripts/manual_tests/version/${VERSION}/|g" "$DOC_FILE"
    sed -i.bak "s|{ROADMAP_LINK}|../../../roadmap/version/${MAJOR_MINOR}/${VERSION}/|g" "$DOC_FILE"
    rm "${DOC_FILE}.bak"
fi

print_success "Created ${DOC_FILE}"

# Summary
echo ""
print_success "Version tests created successfully!"
echo ""
echo "Created files:"
echo "  📁 ${TEST_DIR}/"
echo "     - README.md"
echo "     - smoke_test.py"
for feature in "${FEATURE_ARRAY[@]}"; do
    feature=$(echo "$feature" | xargs)
    echo "     - ${feature}_test.py"
done
echo ""
echo "  📄 ${DOC_FILE}"
echo ""
echo "Next steps:"
echo "  1. Implement tests in ${TEST_DIR}/"
echo "  2. Add test scenarios to ${DOC_FILE}"
echo "  3. Run tests: pytest ${TEST_DIR}/"
echo "  4. Update roadmap and implementation docs with test links"
echo ""
print_success "Done!"
