# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from ..router import router
from ..tasks.tag_needs_review import tag_needs_review


@router.register("check_suite", action="completed")
async def on_pr_green_label_needs_review(event, gh, *args, **kwargs):
    """Add the `needs review` label to the pull requests after the successful
    execution of the CI
    """
    status = event.data["check_suite"]["conclusion"]
    org, repo = event.data["repository"]["full_name"].split("/")
    for pr in event.data["check_suite"]["pull_requests"]:
        tag_needs_review.delay(org, pr["number"], repo, status)
