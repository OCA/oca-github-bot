# Copyright 2026 Maxime Chambreuil - Gray Matter Logic
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

"""Escalate silent PRs: ask a wider human set, never merge."""

from datetime import datetime, timezone

from .. import github
from ..config import GITHUB_LOGIN, GITHUB_ORG, switchable
from ..github import gh_call
from ..queue import getLogger, task

_logger = getLogger(__name__)

BOT_LOGINS = {
    (GITHUB_LOGIN or "").lower(),
    "oca-git-bot",
    "github-actions[bot]",
    "codecov",
    "codecov-commenter",
    "pre-commit-ci[bot]",
}

STEP_MARKERS = (
    "<!-- ocabot-escalate:1 -->",
    "<!-- ocabot-escalate:2 -->",
    "<!-- ocabot-escalate:3 -->",
)

STEP_DELAYS = (7, 14, 21)

PSC_LIST = "https://oca.github.io/repo-maintainer-conf/repos.html"


def _is_bot(login):
    if not login:
        return True
    low = login.lower()
    return low in BOT_LOGINS or low.endswith("[bot]")


def _step_done(bodies, step):
    marker = STEP_MARKERS[step]
    return any(marker in (body or "") for body in bodies)


def next_escalate_step(last_human_at, now, comments_bodies):
    """Return 0, 1 or 2 for the next ping, or None if none is due."""
    if last_human_at is None:
        return None
    elapsed = (now - last_human_at).total_seconds() / 86400
    for step, days in enumerate(STEP_DELAYS):
        if elapsed >= days and not _step_done(comments_bodies, step):
            return step
    return None


def escalate_comment(repo, step):
    team = f"@OCA/{repo}-maintainers"
    if step == 0:
        return (
            f"{STEP_MARKERS[0]}\n"
            f"No human review yet after {STEP_DELAYS[0]} days "
            f"(mechanical checks / `needs review`).\n\n"
            f"Pinging the repo maintainer team: {team}\n"
            "This is not a merge and does not count as a review."
        )
    if step == 1:
        return (
            f"{STEP_MARKERS[1]}\n"
            f"Still no human review after {STEP_DELAYS[1]} days.\n\n"
            "Pinging the PSC for this repository. "
            f"See {PSC_LIST}\n"
            f"(team guess: {team})\n"
            "Please review or say if this should wait. The bot will not merge."
        )
    return (
        f"{STEP_MARKERS[2]}\n"
        f"Still no human review after {STEP_DELAYS[2]} days.\n\n"
        "@OCA/oca-core-maintainers review wanted.\n"
        "Silence escalates who is asked, not who may `/ocabot merge`."
    )


def _comment_dt(comment):
    created = getattr(comment, "created_at", None)
    if created is None:
        return None
    if created.tzinfo is None:
        return created.replace(tzinfo=timezone.utc)
    return created.astimezone(timezone.utc)


def _last_human_at(comments, issue_created):
    last_human = None
    for comment in comments:
        login = comment.user.login if comment.user else None
        if _is_bot(login):
            continue
        created = _comment_dt(comment)
        if created and (last_human is None or created > last_human):
            last_human = created
    if last_human is not None:
        return last_human
    if issue_created is None:
        return None
    if issue_created.tzinfo is None:
        return issue_created.replace(tzinfo=timezone.utc)
    return issue_created.astimezone(timezone.utc)


def _org_repo_from_issue(issue):
    full = issue.html_url  # https://github.com/org/repo/pull/N
    parts = full.split("/")
    return parts[3], parts[4]


@task()
@switchable("escalate_review")
def escalate_review(org=None, dry_run=False):
    """Ping a wider human set when a green PR gets no review."""
    orgs = [org] if org else list(GITHUB_ORG)
    now = datetime.now(timezone.utc)
    with github.login() as gh:
        for org_name in orgs:
            query = [
                "type:pr",
                "state:open",
                'label:"needs review"',
                "-label:approved",
                '-label:"work in progress"',
                '-label:"ready to merge"',
                f"org:{org_name}",
            ]
            for issue in gh.search_issues(" ".join(query)):
                _escalate_one(issue, now, dry_run)


def _escalate_one(issue, now, dry_run):
    comments = list(issue.issue.comments())
    bodies = [c.body or "" for c in comments]
    last_human = _last_human_at(comments, getattr(issue, "created_at", None))
    step = next_escalate_step(last_human, now, bodies)
    if step is None:
        return
    _org_name, repo_name = _org_repo_from_issue(issue)
    body = escalate_comment(repo_name, step)
    if dry_run:
        _logger.info("DRY-RUN escalate step %s on %s", step, issue.html_url)
        return
    _logger.info("escalate step %s on %s", step, issue.html_url)
    gh_call(issue.issue.create_comment, body)
