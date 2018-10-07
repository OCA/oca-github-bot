# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from celery.schedules import crontab

from .queue import app


app.conf.beat_schedule = {
    "heartbeat": {
        "task": "oca_github_bot.tasks.heartbeat.heartbeat",
        "schedule": crontab(minute="*/15"),
    }
}
