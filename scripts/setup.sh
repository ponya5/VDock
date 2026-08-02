#!/usr/bin/env bash
# Compatibility wrapper — prefer the root setup.sh
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$ROOT/setup.sh"
