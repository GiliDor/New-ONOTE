#!/bin/bash
set -euo pipefail

echo "📦 Building ONOTE.app with PyInstaller"

if ! command -v python &>/dev/null; then
  echo "❌ Python not found in PATH" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

echo "🔧 Ensuring dependencies..."
python -m pip install --upgrade pip >/dev/null
python -m pip install pyinstaller >/dev/null

export PYTHONPATH="${PYTHONPATH:-}:$ROOT_DIR/src"

APP_NAME="ONOTE"

echo "🧹 Cleaning previous build"
rm -rf build dist "$APP_NAME.spec" 2>/dev/null || true

echo "🚀 Running PyInstaller"
pyinstaller \
  --noconfirm \
  --windowed \
  --name "$APP_NAME" \
  --osx-bundle-identifier com.onote.app \
  --icon "" \
  run.py

echo "✅ Built: dist/$APP_NAME.app"

