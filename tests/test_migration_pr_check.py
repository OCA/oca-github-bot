# Copyright 2022 Simone Rubino - TAKOBI
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import pytest

from oca_github_bot.tasks.migration_pr_check import is_migration_pr

MIGRATION_PR_PATH = "oca_github_bot.tasks.migration_pr_check"


def _get_addons_gen_mock(pr_new_modules=None):
    """
    Return a callable that returns a list of modules.
    The list contains `pr_new_modules` only after first call.
    """
    if pr_new_modules is None:
        pr_new_modules = list()

    class AddonsGenMock:
        def __init__(self):
            self.addons_gen_calls = 0

        def __call__(self, *args, **kwargs):
            # First time, only the existing addons are returned
            existing_addons = ["existing_addon"]
            if self.addons_gen_calls > 0:
                # After that, return also `pr_new_modules`
                if pr_new_modules:
                    existing_addons.extend(pr_new_modules)
            self.addons_gen_calls += 1
            return existing_addons

    return AddonsGenMock()


@pytest.mark.vcr()
def test_no_new_module(mocker):
    """
    If a PR does not add a new module, then it is not a migration.
    """
    mocker.patch("%s.github" % MIGRATION_PR_PATH)
    mocker.patch("%s.check_call" % MIGRATION_PR_PATH)

    migration_issue = mocker.patch("%s._find_issue" % MIGRATION_PR_PATH)
    migration_issue.return_value.body = "Migration Issue Body"

    addons_gen = mocker.patch("%s.addon_dirs_in" % MIGRATION_PR_PATH)
    addons_gen.side_effect = _get_addons_gen_mock()

    is_migration = is_migration_pr("org", "repo", "pr")
    assert not is_migration


@pytest.mark.vcr()
def test_new_module_no_migration(mocker):
    """
    If a PR adds a new module but the module is not in the migration issue,
    then it is not a migration.
    """
    mocker.patch("%s.github" % MIGRATION_PR_PATH)
    mocker.patch("%s.check_call" % MIGRATION_PR_PATH)

    migration_issue_body = """
Modules to migrate:
- [ ] a_module
    """
    migration_issue = mocker.patch("%s._find_issue" % MIGRATION_PR_PATH)
    migration_issue.return_value.body = migration_issue_body

    addons_gen = mocker.patch("%s.addon_dirs_in" % MIGRATION_PR_PATH)
    addons_gen.side_effect = _get_addons_gen_mock()

    is_migration = is_migration_pr("org", "repo", "pr")
    assert not is_migration


@pytest.mark.vcr()
def test_new_module_migration(mocker):
    """
    If a PR adds a new module and the module is in the migration issue,
    then it is a migration.
    """
    mocker.patch("%s.github" % MIGRATION_PR_PATH)
    mocker.patch("%s.check_call" % MIGRATION_PR_PATH)

    addon_name = "migrated_module"
    migration_issue_body = f"""
Modules to migrate:
- [ ] {addon_name}
    """
    migration_issue = mocker.patch("%s._find_issue" % MIGRATION_PR_PATH)
    migration_issue.return_value.body = migration_issue_body

    addons_gen = mocker.patch("%s.addon_dirs_in" % MIGRATION_PR_PATH)
    addons_gen.side_effect = _get_addons_gen_mock([addon_name])

    is_migration = is_migration_pr("org", "repo", "pr")
    assert is_migration


@pytest.mark.vcr()
def test_migration_comment(mocker):
    """
    If a PR adds a new module and it is in the migration issue,
    then it is a migration.
    """
    github_mock = mocker.patch("%s.github" % MIGRATION_PR_PATH)
    mocker.patch("%s.check_call" % MIGRATION_PR_PATH)

    addon_name = "migrated_module"
    migration_issue_body = f"""
Modules to migrate:
- [ ] {addon_name}
    """
    migration_issue = mocker.patch("%s._find_issue" % MIGRATION_PR_PATH)
    migration_issue.return_value.body = migration_issue_body

    addons_gen = mocker.patch("%s.addon_dirs_in" % MIGRATION_PR_PATH)
    addons_gen.side_effect = _get_addons_gen_mock([addon_name])

    gh_context = mocker.MagicMock()
    github_mock_login_cm = github_mock.login.return_value
    github_mock_login_cm.__enter__.return_value = gh_context

    is_migration = is_migration_pr("org", "repo", "pr")
    assert is_migration


@pytest.mark.vcr()
def test_pr_title(mocker):
    """
    If a PR has [MIG] in its Title,
    then it is a migration.
    """
    github_mock = mocker.patch("%s.github" % MIGRATION_PR_PATH)
    mocker.patch("%s.check_call" % MIGRATION_PR_PATH)

    migration_issue_body = """
    Modules to migrate
        """
    migration_issue = mocker.patch("%s._find_issue" % MIGRATION_PR_PATH)
    migration_issue.return_value.body = migration_issue_body

    addons_gen = mocker.patch("%s.addon_dirs_in" % MIGRATION_PR_PATH)
    addons_gen.side_effect = _get_addons_gen_mock(["another_module"])

    pr_title = "[MIG] migrated_module"
    gh_pr = mocker.MagicMock()
    gh_pr.title = pr_title
    gh_repo = mocker.MagicMock()
    gh_repo.pull_request.return_value = gh_pr
    gh_context = mocker.MagicMock()
    gh_context.repository.return_value = gh_repo
    github_mock_login_cm = github_mock.login.return_value
    github_mock_login_cm.__enter__.return_value = gh_context

    is_migration = is_migration_pr("org", "repo", "pr")
    assert is_migration
