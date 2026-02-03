#!/usr/bin/env bash
set -euo pipefail
BASEDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

find_git_files() {
  local repo
  for repo in "$@"; do git -C "${repo}" ls-files | sed "s|^|${repo}/|"; done
}

cd "${BASEDIR}/../.."
find_git_files browser payments | tar -czf payments/payments.tar.gz --files-from=-
