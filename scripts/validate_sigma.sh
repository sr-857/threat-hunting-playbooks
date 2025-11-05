#!/usr/bin/env bash
set -euo pipefail

if ! command -v sigma-cli &>/dev/null; then
  echo "sigma-cli not found. Install with 'pip install sigma-cli'." >&2
  exit 1
fi

ROOT_DIR="$(dirname "$(dirname "${BASH_SOURCE[0]}")")"
RULE_DIR="${ROOT_DIR}/rules/sigma"

find "${RULE_DIR}" -type f -name '*.yml' \
  -not -path '*/templates/*' \
  -print0 | while IFS= read -r -d '' rule; do
  echo "Validating ${rule}"
  sigma-cli validate "${rule}"
  sigma-cli convert --target splunk "${rule}" >/dev/null
done
