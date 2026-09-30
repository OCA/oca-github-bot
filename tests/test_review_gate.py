# Copyright 2026 Maxime Chambreuil - Gray Matter Logic
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from datetime import datetime, timedelta, timezone
from pathlib import Path

from oca_github_bot.review_gate import check_addon, format_comment, merge_results
from oca_github_bot.tasks.escalate_review import (
    STEP_MARKERS,
    escalate_comment,
    next_escalate_step,
)

from .common import make_addon


def test_missing_development_status_is_blocking(git_clone):
    addon_dir = make_addon(git_clone, "addon_alpha")
    result = check_addon(addon_dir, is_new=False)
    assert result.passed is False
    assert any("development_status" in item for item in result.blocking)


def test_alpha_existing_addon_passes(git_clone):
    addon_dir = make_addon(git_clone, "addon_alpha", development_status="Alpha")
    result = check_addon(addon_dir, is_new=False)
    assert result.passed is True
    assert result.blocking == []


def test_stable_addon_is_warning_not_blocking(git_clone):
    addon_dir = make_addon(
        git_clone, "addon_stable", development_status="Production/Stable"
    )
    result = check_addon(addon_dir, is_new=False)
    assert result.passed is True
    assert any("Production/Stable" in item for item in result.warnings)


def test_new_addon_models_without_acl_is_blocking(git_clone):
    addon_dir = Path(make_addon(git_clone, "addon_new", development_status="Alpha"))
    models = addon_dir / "models"
    models.mkdir()
    (models / "__init__.py").write_text("from . import res_partner\n")
    (models / "res_partner.py").write_text(
        "from odoo import models\n\n"
        "class ResPartner(models.Model):\n"
        "    _name = 'res.partner.extra'\n"
    )
    result = check_addon(str(addon_dir), is_new=True)
    assert result.passed is False
    assert any("ir.model.access.csv" in item for item in result.blocking)


def test_new_addon_with_acl_passes(git_clone):
    addon_dir = Path(make_addon(git_clone, "addon_new", development_status="Alpha"))
    models = addon_dir / "models"
    models.mkdir()
    (models / "res_partner.py").write_text("_name = 'x.y'\n")
    security = addon_dir / "security"
    security.mkdir()
    (security / "ir.model.access.csv").write_text("id,name,model_id:id,group_id:id\n")
    result = check_addon(str(addon_dir), is_new=True)
    assert result.passed is True
    assert any("new addon" in item for item in result.warnings)


def test_format_comment_contains_marker():
    result = merge_results([])
    body = format_comment(result)
    assert "ocabot-review-gate" in body
    assert "not a review" in body.lower() or "volume filter" in body.lower()


def test_escalate_steps_ladder():
    now = datetime(2026, 9, 30, tzinfo=timezone.utc)
    created = now - timedelta(days=8)
    assert next_escalate_step(created, now, []) == 0
    assert next_escalate_step(created, now, [STEP_MARKERS[0]]) is None
    created14 = now - timedelta(days=15)
    assert next_escalate_step(created14, now, [STEP_MARKERS[0]]) == 1
    created21 = now - timedelta(days=22)
    assert next_escalate_step(created21, now, [STEP_MARKERS[0], STEP_MARKERS[1]]) == 2
    assert next_escalate_step(now - timedelta(days=2), now, []) is None


def test_escalate_comment_does_not_claim_merge():
    body = escalate_comment("field-service", 0)
    assert "ocabot-escalate:1" in body
    assert "will not merge" in body.lower() or "not a merge" in body.lower()
    assert "/ocabot merge" in escalate_comment("field-service", 2)
