#!/usr/bin/env bash
set -euo pipefail
BASEDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd ${BASEDIR}/..
FILES=(error* trace* tests/error* test/trace* ../error* ../trace*)

if [[ "${1:-}" == "all" ]]; then
  FILES+=(run/*)
fi

# User globbing protection: run only if files exist
for f in "${FILES[@]}"; do
  if compgen -G "$f" > /dev/null; then
    rm -rf "$f"
  fi
done
