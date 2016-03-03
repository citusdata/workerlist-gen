# workerlist-gen

[![Image Size](https://img.shields.io/imagelayers/image-size/citusdata/workerlist-gen/latest.svg)][image size]
[![Release](https://img.shields.io/github/release/citusdata/workerlist-gen.svg)][release]
[![License](https://img.shields.io/github/license/citusdata/workerlist-gen.svg)][license]

`workerlist-gen` is a simple Docker image intended to run on a container colocated with a Citus master node container. It uses [`docker-gen`][docker-gen] to automatically regenerate the Citus worker list file any time a Citus container is destroyed or added.

## Function

`workerlist-gen` wraps a single `docker-gen` process, which responds to Docker events by regenerating a worker list file. This file will contain the hostnames of all containers with a `com.citusdata.role` label value of `Worker`. All workers are assumed to be running a Citus instance on port `5432`.

The worker list file will be written to `/etc/citus/pg_worker_list.conf` any time the set of worker nodes changes. After updating the file, `docker-gen` will send a `SIGHUP` signal to a container named `citus_master`, useful for prompting a Citus instance to reload its configuration files.

## Usage

Assuming your Docker daemon’s socket is located at `/var/run/docker.sock` (the default), you can start a `workerlist-gen` container like so:

```bash
docker run -v /var/run/docker.sock:/tmp/docker.sock \
  citusdata/workerlist-gen workerlist-gen
```

`docker-gen` expects the Docker daemon’s socket to exist at `/tmp/docker.sock`, so the `-v` flag is needed to ensure it is mounted at that location, though the `DOCKER_HOST` environment variable can be used to override that expectation. The `docker-gen` [project page][docker-gen] providers further details.

### Options

`workerlist-gen` honors a few environment variables in addition to those permitted by [`docker-gen`][docker-gen]…

  * `CITUS_CONFDIR` — Output directory for worker list file (default: `/etc/citus`)
  * `CITUS_CONTAINER` — Container name (or identifier) to signal after configuration changes (default: `citus_master`)

### Real-World Example

Let’s say a Citus container named `citus_master` is already running. The person who started it had the foresight to expose its configuration files as a `VOLUME` at `/etc/citusconf`. That location is non-standard, but nothing `workerlist-gen` can’t handle:

```bash
docker run -v /var/run/docker.sock:/tmp/docker.sock \
  --volumes-from citus_master                       \
  -e CITUS_CONFDIR=/etc/citusconf                   \
  citusdata/workerlist-gen workerlist-gen
```

The `volumes-from` option ensures the `/etc/citusconf` path is shared between the `workerlist-gen` and `citus_master` container, so the configuration is available for reading by the master after `workerlist-gen` sends the `SIGHUP` signal.

## License

Copyright © 2016 Citus Data, Inc.

Licensed under the Apache License, Version 2.0 (the “License”); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

[image size]: https://imagelayers.io/?images=citusdata%2Fworkerlist-gen:latest
[release]: https://github.com/citusdata/workerlist-gen/releases/latest
[license]: LICENSE
[docker-gen]: https://github.com/jwilder/docker-gen
