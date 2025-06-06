#!/usr/bin/env bash
set -euo pipefail

FILES=(error* trace* tests/error* test/trace*)

if [[ "${1:-}" == "all" ]]; then
  FILES+=(run/*)
fi

# Użyj globbing protection: tylko jeśli istnieją pliki
for f in "${FILES[@]}"; do
  if compgen -G "$f" > /dev/null; then
    rm -rf $f
  fi
done
