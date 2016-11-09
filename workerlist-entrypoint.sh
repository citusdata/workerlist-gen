#!/bin/sh

set -e

exec docker-gen -watch -notify-sighup ${CITUS_CONTAINER} \
                /pg_worker_list.tmpl ${CITUS_CONFDIR}/pg_worker_list.conf
