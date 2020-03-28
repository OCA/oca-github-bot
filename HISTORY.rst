20200328
~~~~~~~~

**Features**

- ocabot merge: add a "bot is merging ⏳" PR label during the test
  and merge operation. (`#73 <https://github.com/oca/oca-github-bot/issues/73>`_)
- Add three new settings available in the ``environment`` file that allow to add
  extra argument, when calling the libraries ``oca-gen-addons-table``,
  ``oca-gen-addon-readme`` and ``oca-gen-addon-icon``. (`#103
  <https://github.com/oca/oca-github-bot/issues/103>`_)
- Make the "ocabot merge" command update ``HISTORY.rst`` from news fragments in
  ``readme/newsfragments`` using `towncrier
  <https://pypi.org/project/towncrier/>`_. (`#106
  <https://github.com/oca/oca-github-bot/issues/106>`_)
- Add ``APPROVALS_REQUIRED`` and ``MIN_PR_AGE`` configuration options to
  control the conditions to set the ``Approved`` label. (`#107
  <https://github.com/oca/oca-github-bot/issues/107>`_)


20191226
~~~~~~~~

**Bug fixes**

- do not fail on ``twine check`` when an addon has no ``setup.py``
  `#96 <https://github.com/OCA/oca-github-bot/pull/96>`_

20191126
~~~~~~~~

**Bug fixes**

- do not mention maintainers when they open PR to module they maintain
  `#92 <https://github.com/OCA/oca-github-bot/pull/92>`_
- do not mention maintainers more than once
  `#91 <https://github.com/OCA/oca-github-bot/pull/91>`_

20191027
~~~~~~~~

**Features**

- mention maintainers in pull requests to their addons
  `#77 <https://github.com/OCA/oca-github-bot/pull/77>`_

**Bug fixes**

- main branch bot: do not run on forks on pushes too, not only in cron jobs

**Misc**

- prune removed remote branches in git cache
- make ``git_get_modified_addons`` (use rebase instead of merge)

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
