#!/bin/bash
# ─────────────────────────────────────────────────
# ProTrack — One-click startup script
# Starts MySQL, activates venv, and launches the app
# ─────────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting ProTrack..."
echo "─────────────────────────────────────────"

# ── 1. Start MySQL ────────────────────────────────
echo "📦 Checking MySQL..."
if brew services list | grep -q "mysql.*started"; then
    # Verify it's actually responding
    if mysql -u root -h 127.0.0.1 -P 3306 -e "SELECT 1" &>/dev/null; then
        echo "✅ MySQL is already running"
    else
        echo "⚠️  MySQL service registered but not responding. Restarting..."
        brew services restart mysql
        echo "⏳ Waiting for MySQL to start..."
        for i in {1..15}; do
            if mysql -u root -h 127.0.0.1 -P 3306 -e "SELECT 1" &>/dev/null; then
                echo "✅ MySQL is ready"
                break
            fi
            sleep 1
            if [ "$i" -eq 15 ]; then
                echo "❌ MySQL failed to start after 15 seconds. Please check manually."
                exit 1
            fi
        done
    fi
else
    echo "🔄 Starting MySQL..."
    brew services start mysql
    echo "⏳ Waiting for MySQL to start..."
    for i in {1..15}; do
        if mysql -u root -h 127.0.0.1 -P 3306 -e "SELECT 1" &>/dev/null; then
            echo "✅ MySQL is ready"
            break
        fi
        sleep 1
        if [ "$i" -eq 15 ]; then
            echo "❌ MySQL failed to start after 15 seconds. Please check manually."
            exit 1
        fi
    done
fi

# ── 2. Set up virtual environment ─────────────────
echo "🐍 Setting up Python environment..."
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📥 Installing dependencies..."
    pip install -r requirements-macos.txt
else
    source venv/bin/activate
fi
echo "✅ Virtual environment active ($(python --version))"

# ── 3. Launch ProTrack ────────────────────────────
echo "─────────────────────────────────────────"
echo "🎯 Launching ProTrack..."
echo "   Press Ctrl+C to stop"
echo "─────────────────────────────────────────"
python main.py
