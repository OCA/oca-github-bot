# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from celery.schedules import crontab

from .config import GITHUB_ORG
from .queue import app

beat_schedule = {
    "heartbeat": {
        "task": "oca_github_bot.tasks.heartbeat.heartbeat",
        "schedule": crontab(minute="*/15"),
    }
}

for org in GITHUB_ORG:
    beat_schedule.update(
        {
            "main_branch_bot_all_repos": {
                "task": "oca_github_bot.tasks.main_branch_bot."
                "main_branch_bot_all_repos",
                "args": (org,),
                "kwargs": dict(build_wheels=True),
                "schedule": crontab(hour="2", minute="30"),
            },
            "tag_ready_to_merge": {
                "task": "oca_github_bot.tasks.tag_ready_to_merge.tag_ready_to_merge",
                "args": (org,),
                "schedule": crontab(minute="0"),
            },
        }
    )

app.conf.beat_schedule = beat_schedule
