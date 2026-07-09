"""Tests for the framework configuration engine, sync, and API."""
from __future__ import annotations

import copy

import pytest

from common.exceptions import ConfigValidationError
from frameworks.config import loader
from frameworks.config.schema import validate_config

MINIMAL_CONFIG = {
    "framework": {
        "id": "demo_fw",
        "name": "Demo Framework",
        "version": "1.0",
        "publisher": "Test",
        "category": "Test",
        "description": "d",
        "source_url": "https://example.com",
        "scoring": {
            "status_scores": {"PASS": 1.0, "PARTIAL": 0.5, "FAIL": 0.0, "CANNOT_DETERMINE": 0.0},
            "aggregation": "weighted_mean",
            "cannot_determine_policy": "exclude",
        },
        "controls": [
            {
                "id": "C1",
                "title": "Control 1",
                "description": "c",
                "requirements": [
                    {
                        "identifier": "DEMO-1",
                        "title": "R1",
                        "description": "desc",
                        "control": "ctrl",
                        "weight": 3,
                        "category": "Cat",
                        "evidence_expectations": ["something"],
                        "pass_criteria": "p",
                        "partial_criteria": "pp",
                        "fail_criteria": "f",
                        "references": ["ref"],
                    }
                ],
            }
        ],
    }
}


# --- Schema validation -----------------------------------------------------
def test_valid_config_passes():
    validate_config(MINIMAL_CONFIG)  # should not raise


def test_missing_required_field_rejected():
    bad = copy.deepcopy(MINIMAL_CONFIG)
    del bad["framework"]["scoring"]
    with pytest.raises(ConfigValidationError):
        validate_config(bad)


def test_weight_out_of_range_rejected():
    bad = copy.deepcopy(MINIMAL_CONFIG)
    bad["framework"]["controls"][0]["requirements"][0]["weight"] = 9
    with pytest.raises(ConfigValidationError):
        validate_config(bad)


def test_unknown_property_rejected():
    bad = copy.deepcopy(MINIMAL_CONFIG)
    bad["framework"]["surprise"] = "nope"
    with pytest.raises(ConfigValidationError):
        validate_config(bad)


# --- Loader / normalisation ------------------------------------------------
def test_normalize_flattens_and_orders():
    nf = loader.normalize(MINIMAL_CONFIG)
    assert nf.id == "demo_fw"
    assert nf.requirement_count == 1
    assert nf.requirements[0].control_group == "C1"
    assert nf.requirements[0].order == 0


def test_config_hash_is_deterministic():
    nf1 = loader.normalize(copy.deepcopy(MINIMAL_CONFIG))
    nf2 = loader.normalize(copy.deepcopy(MINIMAL_CONFIG))
    assert nf1.config_hash == nf2.config_hash


def test_duplicate_identifier_rejected():
    bad = copy.deepcopy(MINIMAL_CONFIG)
    dup = copy.deepcopy(bad["framework"]["controls"][0]["requirements"][0])
    bad["framework"]["controls"][0]["requirements"].append(dup)
    with pytest.raises(ConfigValidationError):
        loader.normalize(bad)


def test_all_seed_configs_load():
    frameworks = list(loader.load_all())
    ids = {f.id for f in frameworks}
    assert ids == {"iso_42001", "eu_ai_act", "nist_ai_rmf", "oecd_ai", "owasp_llm"}
    total = sum(f.requirement_count for f in frameworks)
    assert total == 122


# --- Sync ------------------------------------------------------------------
@pytest.mark.django_db
def test_sync_creates_then_idempotent(synced_frameworks):
    from frameworks.models import Framework, Requirement
    from frameworks.services import sync_all

    assert Framework.objects.count() == 5
    assert Requirement.objects.count() == 122
    assert all(r.status == "created" for r in synced_frameworks)

    # Second run: nothing changes.
    again = sync_all()
    assert all(r.status == "unchanged" for r in again)


@pytest.mark.django_db
def test_sync_writes_audit_log(synced_frameworks):
    from audit_logs.models import AuditLog

    assert AuditLog.objects.filter(action="SYNC").count() == 5


# --- API -------------------------------------------------------------------
@pytest.mark.django_db
def test_framework_list_api(api_client, synced_frameworks):
    resp = api_client.get("/api/frameworks")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["meta"]["count"] == 5


@pytest.mark.django_db
def test_framework_detail_api_grouped(api_client, synced_frameworks):
    resp = api_client.get("/api/framework/iso_42001")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["id"] == "iso_42001"
    assert data["requirement_count"] == 34
    assert len(data["controls"]) == 10
    # scoring config surfaced for transparency
    assert data["scoring_config"]["aggregation"] == "weighted_mean"


@pytest.mark.django_db
def test_framework_detail_404(api_client, synced_frameworks):
    resp = api_client.get("/api/framework/does_not_exist")
    assert resp.status_code == 404
    assert resp.json()["success"] is False
