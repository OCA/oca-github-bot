# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import ast
import os
import re

from .github import git_get_current_branch
from .process import check_call, check_output

MANIFEST_NAMES = ("__manifest__.py", "__openerp__.py", "__terp__.py")
VERSION_RE = re.compile(
    r"^(?P<series>\d+\.\d+)\.(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)$"
)
MANIFEST_VERSION_RE = re.compile(
    r"(?P<pre>[\"']version[\"']\s*:\s*[\"'])(?P<version>[\d\.]+)(?P<post>[\"'])"
)


class NoManifestFound(Exception):
    pass


class OdooSeriesNotDetected(Exception):
    pass


def is_addons_dir(addons_dir, installable_only=False):
    """ Test if an directory contains Odoo addons. """
    return any(addon_dirs_in(addons_dir, installable_only))


def is_addon_dir(addon_dir, installable_only=False):
    """ Test if a directory contains an Odoo addon. """
    if not installable_only:
        return bool(get_manifest_path(addon_dir))
    else:
        try:
            return get_manifest(addon_dir).get("installable", True)
        except NoManifestFound:
            return False


def addon_dirs_in(addons_dir, installable_only=False):
    """ Enumerate addon directories """
    for d in os.listdir(addons_dir):
        addon_dir = os.path.join(addons_dir, d)
        if is_addon_dir(addon_dir, installable_only):
            yield addon_dir


def get_addon_name(addon_dir):
    return os.path.basename(os.path.abspath(addon_dir))


def get_manifest_file_name(addon_dir):
    """ Return the name of the manifest file, without path """
    for manifest_name in MANIFEST_NAMES:
        manifest_path = os.path.join(addon_dir, manifest_name)
        if os.path.exists(manifest_path):
            return manifest_name
    return None


def get_manifest_path(addon_dir):
    for manifest_name in MANIFEST_NAMES:
        manifest_path = os.path.join(addon_dir, manifest_name)
        if os.path.exists(manifest_path):
            return manifest_path
    return None


def get_manifest(addon_dir):
    manifest_path = get_manifest_path(addon_dir)
    if not manifest_path:
        raise NoManifestFound(f"no manifest found in {addon_dir}")
    with open(manifest_path, "r") as f:
        return ast.literal_eval(f.read())


def set_manifest_version(addon_dir, version):
    manifest_path = get_manifest_path(addon_dir)
    with open(manifest_path, "r") as f:
        manifest = f.read()
    manifest = MANIFEST_VERSION_RE.sub(r"\g<pre>" + version + r"\g<post>", manifest)
    with open(manifest_path, "w") as f:
        f.write(manifest)


def is_maintainer(username, addon_dirs):
    for addon_dir in addon_dirs:
        try:
            manifest = get_manifest(addon_dir)
        except NoManifestFound:
            return False
        maintainers = manifest.get("maintainers", [])
        if username not in maintainers:
            return False
    return True


def bump_version(version, mode):
    mo = VERSION_RE.match(version)
    if not mo:
        raise RuntimeError(f"{version} does not match the expected version pattern.")
    series = mo.group("series")
    major = mo.group("major")
    minor = mo.group("minor")
    patch = mo.group("patch")
    if mode == "major":
        major = int(major) + 1
        minor = 0
        patch = 0
    elif mode == "minor":
        minor = int(minor) + 1
        patch = 0
    elif mode == "patch":
        patch = int(patch) + 1
    else:
        raise RuntimeError("Unexpected bumpversion mode f{mode}")
    return f"{series}.{major}.{minor}.{patch}"


def bump_manifest_version(addon_dir, mode, git_commit=False):
    version = get_manifest(addon_dir)["version"]
    version = bump_version(version, mode)
    set_manifest_version(addon_dir, version)
    if git_commit:
        addon_name = get_addon_name(addon_dir)
        check_call(
            [
                "git",
                "commit",
                "-m",
                f"{addon_name} {version}",
                "--",
                get_manifest_file_name(addon_dir),
            ],
            cwd=addon_dir,
        )


def git_modified_addons(addons_dir, ref):
    """
    List addons that have been modified in the current branch compared to
    ref, after rebasing on ref.
    Deleted addons are not returned.

    Returns a tuple with a set of modified addons, and a flag telling
    if something else than addons has been modified.
    """
    modified = set()
    current_branch = git_get_current_branch(cwd=addons_dir)
    check_call(["git", "checkout", "-B", "tmp-git-modified-addons"], cwd=addons_dir)
    check_call(["git", "rebase", ref], cwd=addons_dir)
    diffs = check_output(["git", "diff", "--name-only", ref, "--"], cwd=addons_dir)
    check_call(["git", "checkout", current_branch], cwd=addons_dir)
    other_changes = False
    for diff in diffs.split("\n"):
        if not diff:
            continue
        if "/" not in diff:
            # file at repo root modified
            other_changes = True
            continue
        parts = diff.split("/")
        if parts[0] == "setup" and len(parts) > 1:
            addon_name = parts[1]
            if is_addon_dir(
                os.path.join(addons_dir, "setup", addon_name, "odoo_addons", addon_name)
            ) or is_addon_dir(
                os.path.join(
                    addons_dir, "setup", addon_name, "odoo", "addons", addon_name
                )
            ):
                modified.add(addon_name)
            else:
                other_changes = True
        else:
            addon_name = parts[0]
            if is_addon_dir(os.path.join(addons_dir, addon_name)):
                modified.add(addon_name)
            else:
                other_changes = True
    return modified, other_changes


def git_modified_addon_dirs(addons_dir, ref):
    modified_addons, other_changes = git_modified_addons(addons_dir, ref)
    return [os.path.join(addons_dir, addon) for addon in modified_addons], other_changes


def get_odoo_series_from_version(version):
    mo = VERSION_RE.match(version)
    if not mo:
        raise OdooSeriesNotDetected()
    series = mo.group("series")
    if not series:
        raise OdooSeriesNotDetected()
    return tuple(int(s) for s in series.split("."))
