# Copyright 2026 Maxime Chambreuil - Gray Matter Logic
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

"""Mechanical review-gate checks (volume filter, not a human review)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

from .manifest import NoManifestFound, get_addon_name, get_manifest

COMMENT_MARKER = "<!-- ocabot-review-gate -->"
LABEL_BOT_CHECKS_PASSED = "bot checks passed"

STABLE_STATUSES = {"Production/Stable", "Mature"}
MODEL_NAME_RE = re.compile(r"""_name\s*=\s*['"]([a-z0-9.]+)['"]""")


@dataclass
class GateResult:
    blocking: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.blocking


def _has_models(addon_dir: str) -> bool:
    models_dir = os.path.join(addon_dir, "models")
    if not os.path.isdir(models_dir):
        return False
    for name in os.listdir(models_dir):
        if name.endswith(".py") and name != "__init__.py":
            return True
    return False


def _defines_models(addon_dir: str) -> bool:
    models_dir = os.path.join(addon_dir, "models")
    if not os.path.isdir(models_dir):
        return False
    for root, _dirs, files in os.walk(models_dir):
        for name in files:
            if not name.endswith(".py"):
                continue
            path = os.path.join(root, name)
            with open(path, encoding="utf-8", errors="replace") as fh:
                if MODEL_NAME_RE.search(fh.read()):
                    return True
    return False


def _has_acl_file(addon_dir: str) -> bool:
    return os.path.isfile(os.path.join(addon_dir, "security", "ir.model.access.csv"))


def check_addon(addon_dir: str, *, is_new: bool) -> GateResult:
    result = GateResult()
    name = get_addon_name(addon_dir)
    try:
        manifest = get_manifest(addon_dir)
    except NoManifestFound:
        result.blocking.append(f"`{name}`: no `__manifest__.py` found")
        return result
    status = (manifest.get("development_status") or "").strip()
    if not status:
        result.blocking.append(
            f"`{name}`: missing `development_status` in the manifest"
        )
    elif status in STABLE_STATUSES:
        result.warnings.append(
            f"`{name}` has `development_status` {status}; "
            "a human review is required before merge (bot checks are not a review)"
        )
    elif status != "Alpha":
        result.warnings.append(
            f"`{name}` has `development_status` {status} "
            "(not Alpha); keep the normal 2-review path"
        )
    if is_new:
        result.warnings.append(
            f"`{name}` is a new addon on this branch; confirm the name "
            "does not collide with another OCA addon on the same series"
        )
        if _defines_models(addon_dir) and not _has_acl_file(addon_dir):
            result.blocking.append(
                f"`{name}`: new models without `security/ir.model.access.csv` "
                "(obvious ACL hole)"
            )
        elif _has_models(addon_dir) and not _has_acl_file(addon_dir):
            result.warnings.append(
                f"`{name}`: `models/` present but no `security/ir.model.access.csv`"
            )
    return result


def merge_results(results: list[GateResult]) -> GateResult:
    merged = GateResult()
    for result in results:
        merged.blocking.extend(result.blocking)
        merged.warnings.extend(result.warnings)
    return merged


def format_comment(result: GateResult) -> str:
    lines = [
        COMMENT_MARKER,
        "## Mechanical checks",
        "",
        (
            "This is a **volume filter**, not a review. "
            "It does not count as an approval and the bot will not merge."
        ),
        "",
    ]
    if result.passed:
        lines.append("**Result:** ready for a human reviewer / maintainer.")
    else:
        lines.append(
            "**Result:** not ready for reviewers yet. "
            "Please fix the blocking items; maintainers will not be pinged "
            "for review while this stays red (when the first-filter is enabled)."
        )
    if result.blocking:
        lines.extend(["", "### Must fix"])
        lines.extend(f"- {item}" for item in result.blocking)
    if result.warnings:
        lines.extend(["", "### Please check"])
        lines.extend(f"- {item}" for item in result.warnings)
    lines.extend(
        [
            "",
            (
                "Merge still requires 2 human approvals (or 3 within 5 days) "
                "including a PSC, then `/ocabot merge`."
            ),
            "PSC list: https://oca.github.io/repo-maintainer-conf/repos.html",
        ]
    )
    return "\n".join(lines)
