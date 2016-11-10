### workerlist-gen v2.0.0 (November 9, 2016) ###

* Compatible with Citus 6.0; breaks compatibility with prior versions

* Calls `master_initialize_node_metadata` rather than using `SIGHUP`

### workerlist-gen v1.0.0 (November 9, 2016) ###

* Based on `docker-gen` `v0.7.3`

### workerlist-gen v0.9.0 (March 2, 2016) ###

* Initial release

* Based on `docker-gen` `v0.7.0`

* Monitors Citus worker startup/shutdown

* Regenerates `pg_worker_list.conf` when workers change

* Sends `SIGHUP` to `master`

* Configurable via environment variables
