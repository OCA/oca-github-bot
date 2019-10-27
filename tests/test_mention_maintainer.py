# Copyright 2019 Simone Rubino - Agile Business Group
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import pytest

from oca_github_bot.tasks.mention_maintainer import mention_maintainer

from .common import make_addon


@pytest.mark.vcr()
def test_maintainer_mentioned(git_clone, mocker):
    github_mock = mocker.patch("oca_github_bot.tasks.mention_maintainer.github")
    github_mock.temporary_clone.return_value.__enter__.return_value = str(git_clone)

    addon_name = "addon1"
    addon_dir = make_addon(git_clone, addon_name, maintainers=["themaintainer"])

    modified_addons_mock = mocker.patch(
        "oca_github_bot.tasks.mention_maintainer.git_modified_addon_dirs"
    )
    modified_addons_mock.return_value = [addon_dir], False
    mocker.patch("oca_github_bot.tasks.mention_maintainer.check_call")
    mention_maintainer("org", "repo", "pr")

    github_mock.gh_call.assert_called_once()
    assert "@themaintainer" in github_mock.gh_call.mock_calls[0][1][1]


@pytest.mark.vcr()
def test_no_maintainer_no_mention(git_clone, mocker):
    github_mock = mocker.patch("oca_github_bot.tasks.mention_maintainer.github")
    github_mock.temporary_clone.return_value.__enter__.return_value = str(git_clone)

    addon_name = "addon1"
    addon_dir = make_addon(git_clone, addon_name)

    modified_addons_mock = mocker.patch(
        "oca_github_bot.tasks.mention_maintainer.git_modified_addon_dirs"
    )
    modified_addons_mock.return_value = [addon_dir], False
    mocker.patch("oca_github_bot.tasks.mention_maintainer.check_call")
    mention_maintainer("org", "repo", "pr")

    github_mock.gh_call.assert_not_called()
