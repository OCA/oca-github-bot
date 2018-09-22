# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from collections import defaultdict
from datetime import datetime, timedelta

from .. import github
from ..github import gh_call
from ..queue import getLogger, task

_logger = getLogger(__name__)


APPROVALS_REQUIRED = 2
MIN_PR_AGE = timedelta(days=5)
LABEL_APPROVED = "approved"
LABEL_READY_TO_MERGE = "ready to merge"


@task()
def tag_ready_to_merge(org, repo, pr, dry_run=False):
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
        labels = [l.name for l in gh_issue.labels()]
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
                    gh_call(gh_issue.add_labels, LABEL_APPROVED)
            merge_eta = gh_pr.created_at + MIN_PR_AGE
            pr_is_old_enough = datetime.now(gh_pr.created_at.tzinfo) >= merge_eta
            if pr_is_old_enough:
                if LABEL_READY_TO_MERGE not in labels:
                    if dry_run:
                        _logger.info(
                            f"DRY-RUN add {LABEL_READY_TO_MERGE} "
                            f"label to PR {gh_pr.url}"
                        )
                    else:
                        gh_call(gh_issue.add_labels, LABEL_READY_TO_MERGE)
                        gh_call(
                            gh_pr.create_comment,
                            "This PR has been approved by two reviewers and "
                            "has been created more than 5 days ago. "
                            "It should therefore be ready to merge by a maintainer "
                            "(or a PSC member if the concerned addon has "
                            "no declared maintainer). 🤖",
                        )
            else:
                tag_ready_to_merge.s(org, repo, pr, dry_run).apply_async(eta=merge_eta)
        else:
            if LABEL_APPROVED in labels:
                if dry_run:
                    _logger.info(
                        f"DRY-RUN remove {LABEL_APPROVED} label from PR {gh_pr.url}"
                    )
                else:
                    gh_call(gh_issue.remove_label, LABEL_APPROVED)
            if LABEL_READY_TO_MERGE in labels:
                if dry_run:
                    _logger.info(
                        f"DRY-RUN remove {LABEL_READY_TO_MERGE} "
                        f"label from PR {gh_pr.url}"
                    )
                else:
                    gh_call(gh_issue.remove_label, LABEL_READY_TO_MERGE)
