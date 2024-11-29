# Copyright ACSONE SA/NV 2024
# Distributed under the MIT License (http://opensource.org/licenses/MIT).
import pytest

from oca_github_bot.tasks.label_modified_addons import _label_modified_addons


@pytest.mark.vcr()
def test_label_modified_addons(gh):
    _label_modified_addons(gh, "OCA", "mis-builder", "610", dry_run=False)
