#!/bin/bash
set -Eeuo pipefail

# allow to customize the UID of the gosu user,
# so we can share the same than the host's.
# If no user id is set, we use 999
USER_NAME=${LOCAL_USER_NAME:-oca-github-bot}
USER_ID=${LOCAL_USER_ID:-999}

id -u $USER_NAME &> /dev/null || useradd --shell /bin/bash -u $USER_ID -o -c "" -m $USER_NAME

mkdir -p /app/run
if [ ! "$(stat -c '%U' /app/run)" = "${USER_NAME}" ]; then
  chown -R ${USER_NAME}: /app/run
fi
cd /app/run

if [ -z "${NOGOSU:-}" ] ; then
  echo "Starting with UID : $USER_ID in $PWD"
  exec gosu $USER_NAME "$@"
else
  exec "$@"
fi
