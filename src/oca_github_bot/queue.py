# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import celery
from celery.utils.log import get_task_logger

from . import config

app = celery.Celery(
    broker=config.BROKER_URI,
    broker_connection_retry_on_startup=True,
    broker_conn_retry=True,
)

getLogger = get_task_logger

task = app.task


if config.SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(dsn=config.SENTRY_DSN)
