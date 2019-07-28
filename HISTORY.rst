v20190728
~~~~~~~~~

**Features**

- Build and publish wheels to a PEP 503 simple index. Publishing occurs
  on /ocabot merge with version bump, and after the nightly main branch
  actions.
- Simplify the docker image, removing gosu. Run under user 1000 in
  /var/run by default. Can be influenced using docker --user or similar.
  The default docker-compose.yml needs UID and GID environment variables.

v20190708
~~~~~~~~~
