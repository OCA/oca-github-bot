# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import subprocess


class EventMock:
    __slots__ = ["data"]

    def __init__(self, data):
        self.data = data


def make_addon(git_clone, addon_name, **manifest_keys):
    addon_dir = git_clone / addon_name
    addon_dir.mkdir()
    manifest = dict(name=addon_name, **manifest_keys)
    (addon_dir / "__manifest__.py").write_text(repr(manifest))
    (addon_dir / "__init__.py").write_text("")
    return addon_dir


def commit_addon(git_clone, addon_name):
    addon_dir = git_clone / addon_name
    subprocess.check_call(["git", "add", addon_dir], cwd=git_clone)
    subprocess.check_call(["git", "commit", "-m", f"add {addon_name}"], cwd=git_clone)
