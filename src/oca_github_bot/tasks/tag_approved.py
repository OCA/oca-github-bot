# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from collections import defaultdict

from .. import github
from ..config import APPROVALS_REQUIRED, switchable
from ..github import gh_call
from ..queue import getLogger, task
from .tag_ready_to_merge import LABEL_READY_TO_MERGE, tag_ready_to_merge

_logger = getLogger(__name__)

LABEL_APPROVED = "approved"


@task()
@switchable()
def tag_approved(org, repo, pr, dry_run=False):
    """Add the ``approved`` tag to the given PR if conditions are met.

    Remove it if conditions are not met.
    """
    with github.repository(org, repo) as gh_repo:
        gh_pr = gh_call(gh_repo.pull_request, pr)
        if not gh_pr.mergeable:
            # TODO does this exclude merged and closed pr's?
            # TODO remove approved and ready to merge labels here?
            _logger.info(f"{gh_pr.url} is not mergeable, exiting")
            return
        reviews = list(gh_call(gh_pr.reviews))
        # obtain last review state for each reviewer
        review_state_by_user = {}  # login: last review state
        for review in reviews:
            if review.state == "COMMENTED":
                # ignore "commented" review, as they don't change
                # the review status
                continue
            review_state_by_user[review.user.login] = review.state
        # list users by review status
        review_users_by_state = defaultdict(set)
        for login, state in review_state_by_user.items():
            review_users_by_state[state].add(login)
        gh_issue = gh_call(gh_pr.issue)
        labels = [label.name for label in gh_issue.labels()]
        if (
            len(review_users_by_state["APPROVED"]) >= APPROVALS_REQUIRED
            and not review_users_by_state["CHANGES_REQUESTED"]
        ):
            if LABEL_APPROVED not in labels:
                if dry_run:
                    _logger.info(
                        f"DRY-RUN add {LABEL_APPROVED} label to PR {gh_pr.url}"
                    )
                else:
                    _logger.info(f"add {LABEL_APPROVED} label to PR {gh_pr.url}")
                    gh_call(gh_issue.add_labels, LABEL_APPROVED)
            tag_ready_to_merge.delay(org)
        else:
            # remove approved and ready to merge labels
            if LABEL_APPROVED in labels:
                if dry_run:
                    _logger.info(
                        f"DRY-RUN remove {LABEL_APPROVED} label from PR {gh_pr.url}"
                    )
                else:
                    _logger.info(f"remove {LABEL_APPROVED} label from PR {gh_pr.url}")
                    gh_call(gh_issue.remove_label, LABEL_APPROVED)
            if LABEL_READY_TO_MERGE in labels:
                if dry_run:
                    _logger.info(
                        f"DRY-RUN remove {LABEL_READY_TO_MERGE} "
                        f"label from PR {gh_pr.url}"
                    )
                else:
                    _logger.info(
                        f"remove {LABEL_READY_TO_MERGE} label from PR {gh_pr.url}"
                    )
                    gh_call(gh_issue.remove_label, LABEL_READY_TO_MERGE)
