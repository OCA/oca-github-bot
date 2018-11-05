# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from oca_github_bot.manifest import is_addons_dir


def test_is_addons_dir_empty(tmpdir):
    tmpdir.mkdir("addon")
    assert not is_addons_dir(str(tmpdir))


def test_is_addons_dir_one_addon(tmpdir):
    p = tmpdir.mkdir("addon").join("__manifest__.py")
    p.write("{'name': 'addon'}")
    assert is_addons_dir(str(tmpdir))
