# Copyright 2021 Tecnativa - Víctor Martínez
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import pytest

from oca_github_bot.tasks.migration_issue_bot import (
    _check_line_issue,
    _create_or_find_branch_milestone,
    _find_issue,
    _set_lines_issue,
)


def _get_repository(gh, org, repo):
    return gh.repository(org, repo)


@pytest.mark.vcr()
def test_create_or_find_branch_milestone(gh):
    repo = _get_repository(gh, "OCA", "contract")
    milestone = _create_or_find_branch_milestone(repo, "8.0")
    assert milestone.title == "8.0"


@pytest.mark.vcr()
def test_find_issue(gh):
    repo = _get_repository(gh, "OCA", "contract")
    milestone = _create_or_find_branch_milestone(repo, "14.0")
    issue = _find_issue(repo, milestone, "14.0")
    assert issue.title == "Migration to version 14.0"


@pytest.mark.vcr()
def test_set_lines_issue(gh):
    module = "mis_builder"
    gh_pr_user_login = "sbidoul"
    gh_pr_number = 11

    body_transformation = [
        (
            "Issue with list but not the module\n"
            "- [ ] a_module_1 - By @legalsylvain - #1\n"
            "- [ ] z_module_1 - By @pedrobaeza - #2",
            f"Issue with list but not the module\n"
            f"- [ ] a_module_1 - By @legalsylvain - #1\n"
            f"- [ ] {module} - By @{gh_pr_user_login} - #{gh_pr_number}\n"
            f"- [ ] z_module_1 - By @pedrobaeza - #2",
        ),
        (
            f"Issue with list containing the module\n"
            f"- [x] {module} - By @legalsylvain - #1\n"
            f"- [ ] z_module_1 - By @pedrobaeza - #2",
            f"Issue with list containing the module\n"
            f"- [x] {module} - By @{gh_pr_user_login} - #{gh_pr_number}\n"
            f"- [ ] z_module_1 - By @pedrobaeza - #2",
        ),
        (
            f"Issue with list containing the module with no PR\n"
            f"- [x] {module}\n"
            f"- [ ] z_module_1 - By @pedrobaeza - #2",
            f"Issue with list containing the module with no PR\n"
            f"- [x] {module} - By @{gh_pr_user_login} - #{gh_pr_number}\n"
            f"- [ ] z_module_1 - By @pedrobaeza - #2",
        ),
        (
            "Issue with no list",
            f"Issue with no list\n"
            f"- [ ] {module} - By @{gh_pr_user_login} - #{gh_pr_number}",
        ),
    ]
    for old_body, new_body_expected in body_transformation:
        new_body, _ = _set_lines_issue(gh_pr_user_login, gh_pr_number, old_body, module)
        assert new_body == new_body_expected


@pytest.mark.vcr()
def test_check_line_issue(gh):
    module = "mis_builder"
    gh_pr_user_login = "sbidoul"
    gh_pr_number = 11

    old_body = (
        f"Issue with list containing the module\n"
        f"- [ ] a_module_1 - By @legalsylvain - #1\n"
        f"- [ ] {module} - By @{gh_pr_user_login} - #{gh_pr_number}\n"
        f"- [ ] z_module_1 - By @pedrobaeza - #2"
    )
    new_body_expected = (
        f"Issue with list containing the module\n"
        f"- [ ] a_module_1 - By @legalsylvain - #1\n"
        f"- [x] {module} - By @{gh_pr_user_login} - #{gh_pr_number}\n"
        f"- [ ] z_module_1 - By @pedrobaeza - #2"
    )
    new_body = _check_line_issue(gh_pr_number, old_body)
    assert new_body == new_body_expected
