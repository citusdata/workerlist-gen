### workerlist-gen v0.9.0 (March 2, 2016) ###

* Initial release

* Based on `docker-gen` `v0.7.0`

* Monitors Citus worker startup/shutdown

* Regenerates `pg_worker_list.conf` when workers change

* Sends `SIGHUP` to `master`

* Configurable via environment variables
