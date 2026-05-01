#!/bin/sh
set -e

if [ -n "$FIREBASE_CREDENTIALS" ]; then
    mkdir -p /app/src/credentials
    printf '%s' "$FIREBASE_CREDENTIALS" > "/app/src/credentials/m8-team-${APP_ENV:-dev}-firebase.json"
fi

exec "$@"
