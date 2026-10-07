# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from ..router import router
from ..tasks.tag_approved import tag_approved


@router.register("pull_request", action="converted_to_draft")
@router.register("pull_request", action="ready_for_review")
async def on_pr_draft(event, gh, *args, **kwargs):
    """On conversion of a PR to/from draft, re-evaluate the approved label.

    A draft PR must not keep the ``approved`` and ``ready to merge`` labels,
    and a PR which becomes ready for review may already have enough approvals.
    """
    org, repo = event.data["repository"]["full_name"].split("/")
    pr = event.data["pull_request"]["number"]
    tag_approved.delay(org, repo, pr)
