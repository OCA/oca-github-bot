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

...

Nightly
-------

...

TODO (help wanted)
------------------

Intrastructure
^^^^^^^^^^^^^^

* In case several webhooks handle the same GitHub event,
  avoid that one failing hook prevents others to run.

Hooks and tasks
^^^^^^^^^^^^^^^

* include existing bots here:

  * CLA bot
  * readme generator
  * setup.py generator
  * wheel builder
  * pypi publisher?
  * GitHub team members maintenance

* repository maintenance (see repo creation process - cfr OCA Board), eg

  * travis settings
  * some webhooks (although most webhooks can be put at org level)?

* add a label on PR of new contributors
* see also https://github.com/OCA/maintainer-tools/pull/346
* ...

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
as code formatting convention.
To make sure, local coding convention are respected before
you commit, install
`pre-commit <https://github.com/pre-commit/pre-commit>`_ and
run ``pre-commit install`` after cloning the repository.

To run tests, type ``tox``.

Contributors
============

* Stéphane Bidoul <stephane.bidoul@acsone.eu>

Maintainers
===========

This module is maintained by the OCA.

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.
