#!/usr/bin/env bash

# Runs every assertion-based test/*_test.py (see test/shapes_test.py,
# test/group_test.py, ... for the convention: print "All checks passed." and
# exit 0, or print "N FAILURE(S):" and exit 1). Used locally and by CI
# (.github/workflows/ci-build.yaml).

set -u
cd "$(dirname "$0")/.."

failed=0

for f in test/*_test.py; do
    echo "=== $f ==="
    if ! python3 "$f"; then
        failed=1
    fi
    echo
done

exit $failed
