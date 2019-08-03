next
~~~~

**Features**

- Improved command parser (#53)
- Call external tools with universal_newlines=True for better
  output capture (unicode instead of binary) and, in particular,
  better display of errors in merge bot.
- Better detection of modified addons (using diff after rebase instead
  of diff to merge base).
- merge bot: allow addon maintainers to merge (#51)

**Bug fixes**

- Do not attempt to build wheels for uninstallable addons.
- Fix issue in detecting modified setup directory.

v20190729.1
~~~~~~~~~~~

**Bug fixes**

- Update OCA/maintainer-tools to correctly pin docutils 0.15.1.
- Fix traceback in on_pr_green_label_needs_review.

v20190729
~~~~~~~~~

**Features**

- Build and publish wheels to a PEP 503 simple index. Publishing occurs
  on /ocabot merge with version bump, and after the nightly main branch
  actions.
- Simplify the docker image, removing gosu. Run under user 1000 in
  /var/run by default. Can be influenced using docker --user or similar.
  The default docker-compose.yml needs UID and GID environment variables.

**Bug fixes**

- Merge bot: fix detection of modified addons in case main branch was modified
  since the PR was created.
- Update OCA/maintainer-tools to pin docutils 0.15.1
  (see https://github.com/OCA/maintainer-tools/issues/423).

v20190708
~~~~~~~~~
