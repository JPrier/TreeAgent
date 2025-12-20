#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

COMMAND=${1:-help}
case "$COMMAND" in
  build)
    cargo build --workspace ;;
  test)
    cargo test --workspace ;;
  check)
    cargo check --workspace ;;
  help|*)
    echo "Usage: $0 {build|test|check}" >&2
    exit 1 ;;
esac
