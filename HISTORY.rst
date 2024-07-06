v20240706
~~~~~~~~~

**Bugfixes**

- Fix regression in nightly main branch bot. (`#279 <https://github.com/oca/oca-github-bot/issues/279>`_)
- Upgrade to Python 3.12 (`#293 <https://github.com/oca/oca-github-bot/pull/293>`_)
- Upgrade sentry client
- Upgrade to latest OCA/maintainer-tools


v20231216
~~~~~~~~~

**Features**

- Skip fork repos earlier in main branch bot, for better performance in organisations
  with a large number of forks. (`#277 <https://github.com/oca/oca-github-bot/issues/277>`_)
- Support generating ``pyproject.toml`` instead of ``setup.py`` (`#266 <https://github.com/oca/oca-github-bot/issues/266>`_)
- Upgraded maintainer-tools (`#275 <https://github.com/oca/oca-github-bot/issues/275>`_)
- Look for migration issues in all states in ``/ocabot migration`` command (`#216 <https://github.com/OCA/oca-github-bot/pull/216>`_)

**Bugfixes**

- Start wheel build from an empty directory, to avoid accidentally importing
  python files from the addon root directory during the build process. (`#270 <https://github.com/oca/oca-github-bot/issues/270>`_)
- Fixed rendering of OdooSeriesNotFound exceptions (`#274 <https://github.com/oca/oca-github-bot/issues/274>`_)


v20231013
~~~~~~~~~

**Features**

- Add ``MAIN_BRANCH_BOT_MIN_VERSION`` config option to declare the minimum Odoo series
  for which the main branch bot actions runs. (`#252 <https://github.com/oca/oca-github-bot/issues/252>`_)
- Upgrade to latest ``maintainer-tools``, and use ``oca-gen-addon-readme
  --if-source-changed`` to avoid full regenaration of all readme when we upgrade
  the README generator. (`#256 <https://github.com/oca/oca-github-bot/issues/256>`_)


**Bugfixes**

- Add binutils to Dockerfile to fix pandoc installer. (`#259 <https://github.com/oca/oca-github-bot/issues/259>`_)


v20230619
~~~~~~~~~

**Bugfixes**

- Fix merge command regression introduced in previous release. (`#246 <https://github.com/oca/oca-github-bot/issues/246>`_)
- Sanity check the virtual environment used to build wheels.

v20230617.1
~~~~~~~~~~~

**Bugfixes**

- Fix issue where some command errors where not reported as comments on the PR. (`#244 <https://github.com/oca/oca-github-bot/issues/244>`_)


v20230617
~~~~~~~~~

**Bugfixes**

- ``/ocabot migration``: Automaticaly check line in Migration issue when merging the according Pull Request. (`#192 <https://github.com/oca/oca-github-bot/issues/192>`_)
- ``/ocabot migration``: A new migration PR can overwrite the PR in the migration issue only if the latter is closed. (`#218 <https://github.com/oca/oca-github-bot/issues/218>`_)

v20221019
~~~~~~~~~

**Features**

- When calling ``/ocabot migration`` if a previous Pull Request was referenced in the migration issue, post an alert on the new Pull Request to mention the previous work. (`#191 <https://github.com/oca/oca-github-bot/issues/191>`_)
- Refactored wheel builder, adding support for ``pyproject.toml`` in addon directories,
  towards removing ``setup`` directories. (`#212 <https://github.com/oca/oca-github-bot/issues/212>`_)
- Update pinned dependencies. (`#213 <https://github.com/oca/oca-github-bot/issues/213>`_)


**Bugfixes**

- Search for addons maintainers in all the branches of the current repository. (`#183 <https://github.com/oca/oca-github-bot/issues/183>`_)
- Make the command ``/ocabot migration`` working when migration issue doesn't contain migration module lines. (`#190 <https://github.com/oca/oca-github-bot/issues/190>`_)
- Tweak /ocabot usage presentation. (`#199 <https://github.com/oca/oca-github-bot/issues/199>`_)


v20220518
~~~~~~~~~

**Features**

- Added support for Odoo 15 (via a setuptools-odoo and maintainer-tools update). (`#156 <https://github.com/oca/oca-github-bot/issues/156>`_)

**Bugfixes**

- Fixed the mention to maintainers on new pull requests. Also mention maintainers
  when a PR is reopened. (`#166 <https://github.com/oca/oca-github-bot/issues/166>`_)
- Try to avoid git fetch lock issues and sentry alerts pollution by retrying
  automatically. (`#177 <https://github.com/oca/oca-github-bot/issues/177>`_)
- Reduce error noise by suppressing BranchNotFoundError in then merge branch status
  handler. (`#178 <https://github.com/oca/oca-github-bot/issues/178>`_)
- Consider comment made when reviewing Pull request. It so allow users
  to review and launch commands in a single action. (`#182 <https://github.com/oca/oca-github-bot/issues/182>`_)

**Misc**

- Update dependencies, drop support for python 3.6 and 3.7. Test with python 3.10. `#175
  <https://github.com/oca/oca-github-bot/issues/175>`_


v20211206
~~~~~~~~~

**Bugfixes**

The GitHub token used by the bot could be leaked into GitHub comments on pull requests
in some circumstances. Please upgrade and rotate tokens.

**Features**

- Add "/ocabot migration" command, to link a PR to the migration issue and set the
  milestone. (`#97 <https://github.com/oca/oca-github-bot/issues/97>`_)
- Added support for Odoo 15 (via a setuptools-odoo and maintainer-tools update). (`#156 <https://github.com/oca/oca-github-bot/issues/156>`_)

**Other**

- Improved layer caching in the Dockerfile

20210813
~~~~~~~~

**Feature**

- Dockerfile: new version of oca-gen-addons-table
- Improved dry-run mode for the wheel publisher
- Better handling of non-fresh index pages in wheel publisher
- Do not call for maintainers when the PR does not modifies any addon
- Add /ocabot rebase command

**Other**

- Use Celery 5

20210321
~~~~~~~~

**Feature**

- Upload wheels to a package index with twine.
- Pre-install setuptools-odoo in the docker image, so wheel builds run faster.

20210228
~~~~~~~~

**Features**

- Add a call to maintainers when a PR is made to addons that have no declared
  maintainers. (`#130 <https://github.com/oca/oca-github-bot/issues/130>`_)
- Refresh all pinned dependencies in requirements.txt. (`#140 <https://github.com/oca/oca-github-bot/issues/140>`_)
- Ignore check suites that have no check runs. This should cope repos that have
  no ``.travis.yml`` but where Travis is enabled at organization level. (`#141 <https://github.com/oca/oca-github-bot/issues/141>`_)


20210131
~~~~~~~~

**Features**

- Add the possibility to set multiple github organizations in GITHUB_ORG setting
  (for organization wide scheduled tasks) (`#127 <https://github.com/oca/oca-github-bot/issues/127>`_)
- Build and publish metapackage wheel from ``setup/_metapackage`` in main branch
  bot task. (`#133 <https://github.com/oca/oca-github-bot/issues/133>`_)

**Bugfixes**

- ocabot merge: only mention maintainers existing before the PR. (`#131 <https://github.com/oca/oca-github-bot/issues/131>`_)

**Miscellaneous**

- Upgrade ``setuptools-odoo`` to 2.6.3 in Docker image


20200719
~~~~~~~~

**Features**

- Add more logging of status and check suites results. (`#121 <https://github.com/oca/oca-github-bot/issues/121>`_)
- Publish wheels also in nobump mode. This exception was probably done with the
  goal of saving space, but for migration PRs where people use ``ocabot merge
  nobump``, we want to publish too. (`#123 <https://github.com/oca/oca-github-bot/issues/123>`_)


20200530
~~~~~~~~

**Features**

- Ignore Dependabot by default in check-suite ignores, along with Codecov. (`#115 <https://github.com/oca/oca-github-bot/issues/115>`_)


**Bugfixes**

- Update maintainer-tools to get the latest ``oca-gen-addon-tables``. It fixes a
  regression where the main branch operations were failing when ``README.md`` is
  absent. (`#118 <https://github.com/oca/oca-github-bot/issues/118>`_)


20200415
~~~~~~~~

**Features**

- Make ``bumpversion_mode`` option required on ``merge`` command, adding ``nobump`` option that was before implicit.
  Bot adds comment on github, if the command is wrong. Message are customizable in the ``environment`` file. (`#90 <https://github.com/oca/oca-github-bot/issues/90>`_)
- Make ``GITHUB_STATUS_IGNORED`` and ``GITHUB_CHECK_SUITES_IGNORED`` configurable. (`#111 <https://github.com/oca/oca-github-bot/issues/111>`_)
- Add ``BOT_TASKS_DISABLED``. (`#112 <https://github.com/oca/oca-github-bot/issues/112>`_)


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
