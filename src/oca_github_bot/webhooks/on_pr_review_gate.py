# Copyright 2026 Maxime Chambreuil - Gray Matter Logic
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from ..router import router
from ..tasks.review_gate import review_gate


@router.register("pull_request", action="opened")
@router.register("pull_request", action="reopened")
@router.register("pull_request", action="synchronize")
async def on_pr_review_gate(event, *args, **kwargs):
    """Run mechanical checks whenever the PR is opened or updated."""
    org, repo = event.data["repository"]["full_name"].split("/")
    pr = event.data["pull_request"]["number"]
    review_gate.delay(org, repo, pr)
