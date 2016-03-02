#!/bin/bash

# make bash behave
set -euo pipefail
IFS=$'\n\t'

exec docker-gen -watch -notify-sighup ${CITUS_CONTAINER} \
                /pg_worker_list.tmpl ${CITUS_CONFDIR}/pg_worker_list.conf
