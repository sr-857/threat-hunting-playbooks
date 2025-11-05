#!/usr/bin/env bash
set -euo pipefail

if ! command -v yarac &>/dev/null; then
  echo "yarac not found. Install YARA CLI tools." >&2
  exit 1
fi

ROOT_DIR="$(dirname "$(dirname "${BASH_SOURCE[0]}")")"
RULE_DIR="${ROOT_DIR}/rules/yara"

find "${RULE_DIR}" -type f -name '*.yar' \
  -not -path '*/templates/*' \
  -print0 | while IFS= read -r -d '' rule; do
  echo "Compiling ${rule}"
  tmp_compiled="$(mktemp)"
  if ! yarac "${rule}" "${tmp_compiled}"; then
    rm -f "${tmp_compiled}"
    exit 1
  fi
  rm -f "${tmp_compiled}"
done
