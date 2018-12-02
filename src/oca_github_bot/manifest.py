# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import ast
import os
import re
import subprocess

MANIFEST_NAMES = ("__manifest__.py", "__openerp__.py", "__terp__.py")
VERSION_RE = re.compile(
    r"^(?P<series>\d+\.\d+)\.(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)$"
)
MANIFEST_VERSION_RE = re.compile(
    r"(?P<pre>[\"']version[\"']\s*:\s*[\"'])(?P<version>[\d\.]+)(?P<post>[\"'])"
)


class NoManifestFound(Exception):
    pass


def is_addons_dir(addons_dir):
    """ Test if an directory contains Odoo addons. """
    if not os.path.isdir(addons_dir):
        return False
    for p in os.listdir(addons_dir):
        addon_dir = os.path.join(addons_dir, p)
        if not os.path.isdir(addon_dir):
            continue
        if is_addon_dir(addon_dir):
            return True
    return False


def is_addon_dir(addon_dir):
    """ Test if a directory contains an Odoo addon. """
    return bool(get_manifest_path(addon_dir))


def get_manifest_path(addon_dir):
    for manifest_name in MANIFEST_NAMES:
        manifest_path = os.path.join(addon_dir, manifest_name)
        if os.path.exists(manifest_path):
            return manifest_path
    return None


def get_manifest(addon_dir):
    manifest_path = get_manifest_path(addon_dir)
    if not manifest_path:
        raise NoManifestFound()
    with open(manifest_path, "r") as f:
        return ast.literal_eval(f.read())


def set_manifest_version(addon_dir, version):
    manifest_path = get_manifest_path(addon_dir)
    with open(manifest_path, "r") as f:
        manifest = f.read()
    manifest = MANIFEST_VERSION_RE.sub(r"\g<pre>" + version + r"\g<post>", manifest)
    with open(manifest_path, "w") as f:
        f.write(manifest)


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
    elif mode == "minor":
        minor = int(minor) + 1
    elif mode == "patch":
        patch = int(patch) + 1
    else:
        raise RuntimeError("Unexpected bumpversion mode f{mode}")
    return f"{series}.{major}.{minor}.{patch}"


def bump_manifest_version(addon_dir, mode):
    version = get_manifest(addon_dir)["version"]
    version = bump_version(version, mode)
    set_manifest_version(addon_dir, version)


def git_modified_addons(addons_dir, ref):
    """
    List addons that have been modified in git HEAD compared to ref.
    """
    modified = set()
    cmd = ["git", "diff", "--name-only", ref]
    diffs = subprocess.check_output(cmd, cwd=addons_dir, universal_newlines=True)
    for diff in diffs.split("\n"):
        if not diff or "/" not in diff:
            continue
        parts = diff.split("/")
        if parts[0] == "setup" and len(parts) > 1:
            addon_name = parts[1]
            if os.path.isdir(os.path.join(addons_dir, "setup", addon_name)):
                modified.add(addon_name)
        else:
            addon_name = parts[0]
            if is_addon_dir(os.path.join(addons_dir, addon_name)):
                modified.add(addon_name)
    return modified
