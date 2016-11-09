FROM jwilder/docker-gen:0.7.3
MAINTAINER Citus Data https://citusdata.com

ENV CITUS_CONFDIR=/etc/citus \
    CITUS_CONTAINER=citus_master

VOLUME $CITUS_CONFDIR

COPY workerlist-entrypoint.sh pg_worker_list.tmpl /

ENTRYPOINT ["/workerlist-entrypoint.sh"]
