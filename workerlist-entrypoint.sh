#!/bin/sh

set -e
PSQL_CMD="psql -h/var/run/postgresql -Upostgres"
REFRESH_CMD="${PSQL_CMD} -c 'SELECT master_initialize_node_metadata();'"

exec docker-gen -watch -notify "${REFRESH_CMD}" \
                /pg_worker_list.tmpl ${CITUS_CONFDIR}/pg_worker_list.conf
