#!/usr/bin/env bash
# Render 배포용 시작 스크립트
set -e
cd "$(dirname "$0")/backend"
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
