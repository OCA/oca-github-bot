# Copyright (c) Alexandre Fayolle 2019
# Distributed under the MIT License (http://opensource.org/licenses/MIT).
import os

import pytest
import vcr

from oca_github_bot import cla, config, github


@pytest.fixture
def cla_cache_db():
    config.CLABOT_CACHE = "test_cla.sqlite"
    if os.path.isfile(config.CLABOT_CACHE):
        os.unlink(config.CLABOT_CACHE)
    cla.init_cla_database(config.CLABOT_CACHE)
    # if updating the tests, please change the values below to something that
    # will work, and don't forget to edit them out of the vcr cassette!
    config.GITHUB_LOGIN = "gurneyalex"
    config.GITHUB_TOKEN = "123456789abcdef123456789abcdef123456789a"
    config.ODOO_LOGIN = "clabot"
    config.ODOO_PASSWORD = "totallyfake"
    config.ODOO_DB = "odoo_community_v11"


def test_clachecker(cla_cache_db, mocker):
    mocker.patch("oca_github_bot.github.gh_comment_issue")
    checker = cla.CLAChecker(
        "gurneyalex", "server-tools", "gurneyalex", 1, "synchronize"
    )
    with vcr.use_cassette("tests/vcr_cassettes/server-tools_pr1.yaml"):
        checker.check_cla()
    expected_msg = """Hey @gurneyalex,
thank you for your Pull Request and contribution to the OCA.

It looks like some users haven't signed our **C**ontributor **L**icense
**A**greement, yet.

1. You can get our full Contributor License Agreement (CLA) here:
http://odoo-community.org/page/website.cla

2. Your company (with Enterprise CLA) or every users listed below (with
Individual CLA) should complete and sign it

3. Do not forget to include your complete data (company and/or personal) and
the covered Github login(s).

4. Please scan the document(s) and send them back to cla@odoo-community.org,

Here is a list of the users :
+ @oca-transbot
+ @Emiq2 (login unknown in OCA database)

Appreciation of efforts,

--
OCA CLAbot"""
    github.gh_comment_issue.assert_called_once_with(
        "gurneyalex", "server-tools", 1, expected_msg
    )
