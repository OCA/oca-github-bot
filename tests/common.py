# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import subprocess
from contextlib import contextmanager

from oca_github_bot import config


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
    return str(addon_dir)


def commit_addon(git_clone, addon_name):
    addon_dir = git_clone / addon_name
    subprocess.check_call(["git", "add", addon_dir], cwd=git_clone)
    subprocess.check_call(
        ["git", "commit", "-m", f"[BOT] add {addon_name}"], cwd=git_clone
    )


@contextmanager
def set_config(**kwargs):
    saved = {}
    for key in kwargs:
        saved[key] = getattr(config, key)
        setattr(config, key, kwargs[key])
    try:
        yield
    finally:
        for key in saved:
            setattr(config, key, kwargs[key])
