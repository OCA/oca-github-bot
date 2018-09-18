# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import logging

import celery
from celery.utils.log import get_task_logger

from . import config

app = celery.Celery(broker=config.REDIS_URI)

getLogger = get_task_logger

task = app.task


if config.SENTRY_DSN:
    from raven import Client
    from raven.contrib.celery import register_signal, register_logger_signal

    client = Client(config.SENTRY_DSN)

    # register a custom filter to filter out duplicate logs
    register_logger_signal(client, loglevel=logging.WARNING)

    # The register_signal function can also take an optional argument
    # `ignore_expected` which causes exception classes specified in Task.throws
    # to be ignored
    register_signal(client, ignore_expected=True)
