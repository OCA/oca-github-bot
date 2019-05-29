##############
OCA GitHub bot
##############

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

On Pull Request review
----------------------

When there are two approvals, set the ``approved`` label.
When the PR is at least 5 days old, set the ``ready to merge`` label.

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

First create and customize a file named ``environment``,
based on `environment.sample <./environment.sample>`_.

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

Contributors
============

* Stéphane Bidoul <stephane.bidoul@acsone.eu>
* Holger Brunn <hbrunn@therp.nl>
* Michel Raich <miquel.raich@eficent.com>
* Florian Kantelberg <florian.kantelberg@initos.com>

Maintainers
===========

This module is maintained by the OCA.

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.
