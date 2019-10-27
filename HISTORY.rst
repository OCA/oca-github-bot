unreleased
~~~~~~~~~~

**Bug fixes**

- main branch bot: do not run on forks on pushes too, not only in cron jobs

20191017
~~~~~~~~

**Bug fixes**

- Ignore /ocabot merge commands in quoted replies (lines starting with >).

**Misc**

- Better logging of subprocess output, for Sentry support.
- Do not change current directory so a multithreaded task worker should be safe.

20191004
~~~~~~~~

**Misc**

- Bump setuptools-odoo version for Odoo 13 support.

20190923
~~~~~~~~

**Bug fixes**

- Do not bump version nor attempt to generate wheels for addons
  that are not installable.

20190904.1
~~~~~~~~~~

**Features**

- Improved command parser (#53)
- Call external tools with universal_newlines=True for better
  output capture (unicode instead of binary) and, in particular,
  better display of errors in merge bot.
- Better detection of modified addons (using diff after rebase instead
  of diff to merge base).
- merge bot: allow addon maintainers to merge (#51)
- main branch bot: ignore repos that are forks of other repos when
  running the main branch bot actions in the nightly cron
- main branch bot: do not run the organization-wide nightly crons if
  GITHUB_ORG is not set
- merge bot: do not rebase anymore, create a merge commit

**Bug fixes**

- Do not attempt to build wheels for uninstallable addons.
- Fix issue in detecting modified setup directory.
- When rsyncing wheels to the simple index, use default directory
  permissions on the target

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
