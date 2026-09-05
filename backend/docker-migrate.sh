#!/bin/sh
set -eu

attempt=1
max_attempts=20

until alembic upgrade head; do
  if [ "$attempt" -ge "$max_attempts" ]; then
    echo "Database migration failed after $max_attempts attempts." >&2
    exit 1
  fi

  echo "Database is not ready; retrying migration in 3 seconds." >&2
  attempt=$((attempt + 1))
  sleep 3
done
