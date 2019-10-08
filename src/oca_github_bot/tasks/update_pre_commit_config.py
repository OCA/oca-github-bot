import re
import shutil
import subprocess
from pathlib import Path

from ..github import git_commit_if_needed
from ..manifest import addon_dirs_in, get_addon_name, is_addon_dir
from ..process import check_call


def _uninstallable_addons(target):
    for addon_dir in addon_dirs_in(target):
        if not is_addon_dir(addon_dir, installable_only=True):
            yield get_addon_name(addon_dir)


def _pre_commit_exclude_uninstallable_addons(target):
    pre_commit_path = target / ".pre-commit-config.yaml"
    if not pre_commit_path.exists():
        return
    exclude = "|".join(
        f"^{addon_name}/" for addon_name in sorted(_uninstallable_addons(target))
    )
    if exclude:
        with open(pre_commit_path) as f:
            pre_commit = f.read()
        pre_commit = re.sub(
            r"^exclude: (.*?$(?!.^ ))",
            f"exclude: \\1|\n  {exclude}",
            pre_commit,
            flags=re.MULTILINE | re.DOTALL,
        )
        with open(pre_commit_path, "w") as f:
            f.write(pre_commit)


def _copy_pre_commit_config(source, target):
    filenames = []
    for filename in source.glob("*"):
        shutil.copy(filename, target)
        filenames.append(filename.name)
    return filenames


def _pre_commit_run(target):
    for _ in range(3):
        r = subprocess.call(["pre-commit", "run", "-a"], cwd=target)
        if r == 0:
            return True
    return False


def _update_pre_commit_config(source, target, commit_message, files_to_remove=None):
    source = Path(source)
    target = Path(target)
    filenames = _copy_pre_commit_config(source, target)
    _pre_commit_exclude_uninstallable_addons(target)
    if files_to_remove:
        check_call(
            ["git", "rm", "--ignore-unmatch", "--"] + files_to_remove, cwd=target
        )
    # git add pre-commit configuration files, including new ones
    check_call(["git", "add", "--"] + filenames, cwd=target)
    success = _pre_commit_run(target)
    # git add files modified by the pre-commit run, if any
    check_call(["git", "add", "-u"], cwd=target)
    if success:
        git_commit_if_needed(commit_message, cwd=target)
    return success
