#!/bin/bash

echo "🚀 Starting Complaints Processing API..."

echo "📊 Configuration:"
echo "  DB_NAME: ${DB_NAME:-/app/data/complaints.db}"
echo "  HOST: ${HOST:-0.0.0.0}"
echo "  PORT: ${PORT:-8000}"
echo "  DEBUG: ${DEBUG:-false}"

echo "🎯 Starting API server..."
uvicorn src.api_app:app --host 0.0.0.0 --port 8000