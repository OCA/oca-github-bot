##############
OCA GitHub bot
##############

.. image:: https://results.pre-commit.ci/badge/github/OCA/oca-github-bot/master.svg
   :target: https://results.pre-commit.ci/latest/github/OCA/oca-github-bot/master
   :alt: pre-commit.ci status
.. image:: https://github.com/OCA/oca-github-bot/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/OCA/oca-github-bot/actions/workflows/ci.yml
   :alt: GitHub CI status

The goal of this project is to collect in one place:

* all operations that react to GitHub events,
* all operations that act on GitHub repos on a scheduled basis.

This will make it easier to review changes, as well as monitor and manage
these operations, compared to the current situations where these functions
are spread across cron jobs and ad-hoc scripts.

**Table of contents**

.. contents::
   :local:

Features
========

On pull request open
--------------------

Mention declared maintainers that addons they maintain are being modified.

Comment with a call for maintainers if there are no declared maintainer.

On pull request close
---------------------

Auto-delete pull request branch
  When a pull request is merged from a branch in the same repo,
  the bot deletes the source branch.

On push to main branches
------------------------

Repo addons table generator in README.md
  For addons repositories, update the addons table in README.md.

Addon README.rst generator
  For addons repositories, generate README.rst from readme fragments
  in each addon directory, and push changes back to github.

Addon icon generator
  For addons repositories, put default OCA icon in each addon that don't have
  yet any icon, and push changes back to github.

setup.py generator
  For addons repositories, run setuptools-odoo-make-defaults, and push
  changes back to github.

These actions are also run nightly on all repos.

Also nightly, wheels are generated for all addons repositories and rsynced
to a PEP 503 simple index or twine uploaded to compatible indexes.

On Pull Request review
----------------------

When there are two approvals, set the ``approved`` label.
When the PR is at least 5 days old, set the ``ready to merge`` label.

On Pull Request CI status
-------------------------

When the CI in a Pull Request goes green, set the ``needs review`` label,
unless it has ``wip:``  or ``[wip]`` in it's title.

Commands
--------

One can ask the bot to perform some tasks by entering special commands
as merge request comments.

``/ocabot merge`` followed by one of ``major``, ``minor``, ``patch`` or ``nobump``
can be used to ask the bot to do the following:

* merge the PR onto a temporary branch created off the target branch
* merge when tests on the rebased branch are green
* optionally bump the version number of the addons modified by the PR
* when the version was bumped, udate the changelog with ``oca-towncrier``
* run the main branch operations (see above) on it
* when the version was bumped, generate a wheel, rsync it to a PEP 503
  simple index root, or upload it to one or more indexes with twine

``/ocabot rebase`` can be used to ask the bot to do the following:

* rebase the PR on the target branch

``/ocabot migration``, followed by the module name, performing the following:

* Look for an issue in that repository with the name "Migration to version
  ``{version}``", where ``{version}`` is the name of the target branch.
* Add or edit a line in that issue, linking the module to the pull request
  (PR) and the author of it.
* TODO: When the PR is merged, the line gets ticked.
* Put the milestone corresponding to the target branch in the PR.

TODO (help wanted)
------------------

See our open `issues <https://github.com/OCA/oca-github-bot/issues>`_,
pick one and contribute!


Developing new features
=======================

The easiest is to look at examples.

New webhooks are added in the `webhooks <./src/oca_github_bot/webhooks>`_ directory.
Webhooks execution time must be very short and they should
delegate the bulk of their work as delayed tasks, which have
the benefit of not overloading the machine and having proper
error handling and monitoring.

Tasks are in the `tasks <./src/oca_github_bot/tasks>`_ directory. They are `Celery tasks
<http://docs.celeryproject.org/en/latest/userguide/tasks.html>`_.

Tasks can be scheduled, in `cron.py <./src/oca_github_bot/cron.py>`_, using the `Celery periodic tasks
<http://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html>`_ mechanism.

Running it
==========

Environment variables
---------------------

First create and customize a file named ``.env``,
based on `environment.sample <./environment.sample>`_.

Tasks performed by the bot can be specified by setting the ``BOT_TASKS``
variable. This is useful if you want to use this bot for your own GitHub
organisation.

You can also disable a selection of tasks, using ``BOT_TASKS_DISABLED``.

Using docker-compose
--------------------

``docker-compose up --build`` will start

* the bot, listening for webhooks calls on port 8080
* a celery ``worker`` to process long running tasks
* a celery ``beat`` to launch scheduled tasks
* a ``flower`` celery monitoring tool on port 5555

The bot URL must be exposed on the internet through a reverse
proxy and configured as a GitHub webhook, using the secret configured
in ``GITHUB_SECRET``.

Development
===========

This project uses `black <https://github.com/ambv/black>`_
as code formatting convention, as well as isort and flake8.
To make sure local coding convention are respected before
you commit, install
`pre-commit <https://github.com/pre-commit/pre-commit>`_ and
run ``pre-commit install`` after cloning the repository.

To run tests, type ``tox``. Test are written with pytest.

Here is a recommended procedure to test locally:

* Prepare an ``environment`` file by cloning and adapting ``environment.sample``.
* Load ``environment`` in your shell, for instance with bash:

.. code::

  set -o allexport
  source environment
  set +o allexport

* Launch the ``redis`` message queue:

.. code::

  docker run -p 6379:6379 redis

* Install the `maintainer tools <https://github.com/OCA/maintainer-tools>`_ and add the generated binaries to your path:

.. code::

  PATH=/path/to/maintainer-tools/env/bin/:$PATH

* Create a virtual environment and install the project in it:

.. code::

  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt -e .

* Then you can debug the two processes in your favorite IDE:

  - the webhook server: ``python -m oca_github_bot``
  - the task worker: ``python -m celery --app=oca_github_bot.queue.app  worker --pool=solo --loglevel=INFO``

* To expose the webhook server on your local machine to internet,
  you can use `ngrok <https://ngrok.com/>`_
* Then configure a GitHub webhook in a sandbox project in your organization
  so you can start receiving webhook calls to your local machine.

Releasing
=========

To release a new version, follow these steps:
- ``towncrier --version YYYYMMDD``
- git commit the updated `HISTORY.rst` and removed newfragments
- ``git tag vYYYYMMDD``
- ``git push --tags``

Contributors
============

* Stéphane Bidoul <stephane.bidoul@acsone.eu>
* Holger Brunn <hbrunn@therp.nl>
* Miquel Raïch <miquel.raich@forgeflow.com>
* Florian Kantelberg <florian.kantelberg@initos.com>
* Laurent Mignon <laurent.mignon@acsone.eu>
* Jose Angel Fentanez <joseangel@vauxoo.com>
* Simone Rubino <simone.rubino@agilebg.com>
* Sylvain Le Gal (https://twitter.com/legalsylvain)
* Tecnativa - Pedro M. Baeza
* Tecnativa - Víctor Martínez

Maintainers
===========

This module is maintained by the OCA.

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.
