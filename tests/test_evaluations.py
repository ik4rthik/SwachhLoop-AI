"""
SwachhLoop AI — Phase 5 AI Evaluation Framework Unit & Integration Tests
========================================================================
Tests for:
  - Metric computation functions (classification, route constraints, RAG grounding, workflows)
  - Individual evaluators (complaint, waste, route, verification, RAG, workflow)
  - Full evaluation runner execution and JSON report generation
"""

import json
from pathlib import Path
import pytest

from evaluations.metrics import (
    compute_classification_metrics,
    compute_route_evaluation_metrics,
    compute_rag_evaluation_metrics,
    compute_workflow_evaluation_metrics,
)
from evaluations.evaluators.complaint_evaluator import ComplaintEvaluator
from evaluations.evaluators.waste_evaluator import WasteDetectionEvaluator
from evaluations.evaluators.route_evaluator import RouteEvaluator
from evaluations.evaluators.verification_evaluator import VerificationEvaluator
from evaluations.evaluators.rag_evaluator import RAGEvaluator
from evaluations.evaluators.workflow_evaluator import WorkflowEvaluator
from evaluations.runner import run_all_evaluations


# ===========================================================================
# 1. Metric Calculations Tests
# ===========================================================================

def test_compute_classification_metrics_perfect():
    y_true = ["critical", "high", "low"]
    y_pred = ["critical", "high", "low"]
    res = compute_classification_metrics(y_true, y_pred)
    assert res["accuracy"] == 1.0
    assert res["macro_f1"] == 1.0
    assert res["macro_precision"] == 1.0
    assert res["macro_recall"] == 1.0
    assert res["sample_count"] == 3


def test_compute_classification_metrics_imperfect():
    y_true = ["critical", "high", "low", "medium"]
    y_pred = ["critical", "low", "low", "medium"]
    res = compute_classification_metrics(y_true, y_pred)
    assert res["accuracy"] == 0.75
    assert "critical" in res["per_class"]
    assert res["per_class"]["critical"]["precision"] == 1.0


def test_compute_route_evaluation_metrics():
    records = [
        {"has_violations": False, "optimized_distance_km": 8.0, "naive_distance_km": 10.0, "optimized_duration_min": 30.0},
        {"has_violations": True, "optimized_distance_km": 12.0, "naive_distance_km": 12.0, "optimized_duration_min": 45.0},
    ]
    res = compute_route_evaluation_metrics(records)
    assert res["total_routes_evaluated"] == 2
    assert res["constraint_violation_count"] == 1
    assert res["constraint_violation_rate"] == 0.5
    assert res["average_distance_reduction_pct"] == 10.0  # (20% + 0%) / 2


def test_compute_rag_evaluation_metrics():
    records = [
        {
            "is_in_domain": True,
            "found_knowledge": True,
            "expected_article_id": "kb_01",
            "retrieved_article_ids": ["kb_01", "kb_02"],
            "relevance_score": 0.8,
            "grounding_score": 0.85,
        },
        {
            "is_in_domain": False,
            "found_knowledge": False,  # correct rejection
            "relevance_score": 0.0,
            "grounding_score": 0.0,
        },
    ]
    res = compute_rag_evaluation_metrics(records)
    assert res["total_queries_evaluated"] == 2
    assert res["citation_coverage_rate"] == 1.0
    assert res["fallback_accuracy"] == 1.0


def test_compute_workflow_evaluation_metrics():
    records = [
        {"status": "COMPLETED", "requires_human_review": False, "expected_human_review": False, "latency_ms": 10.0},
        {"status": "NEEDS_REVIEW", "requires_human_review": True, "expected_human_review": True, "latency_ms": 12.0},
    ]
    res = compute_workflow_evaluation_metrics(records)
    assert res["total_workflows"] == 2
    assert res["success_rate"] == 1.0
    assert res["human_review_accuracy"] == 1.0
    assert res["mean_latency_ms"] == 11.0


# ===========================================================================
# 2. Individual Evaluators Execution Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_complaint_evaluator():
    evaluator = ComplaintEvaluator()
    res = await evaluator.evaluate()
    assert res["sample_count"] > 0
    assert "urgency_accuracy" in res["metrics"]
    assert "location_extraction_accuracy" in res["metrics"]
    assert res["dataset_type"] == "offline_synthetic_fixtures"


@pytest.mark.asyncio
async def test_waste_evaluator():
    evaluator = WasteDetectionEvaluator()
    res = await evaluator.evaluate()
    assert res["sample_count"] > 0
    assert "detection_accuracy" in res["metrics"]
    assert "bounding_box_validity_rate" in res["metrics"]


@pytest.mark.asyncio
async def test_route_evaluator():
    evaluator = RouteEvaluator()
    res = await evaluator.evaluate()
    assert res["sample_count"] > 0
    assert "constraint_violation_rate" in res["metrics"]
    assert res["metrics"]["constraint_violation_rate"] == 0.0


@pytest.mark.asyncio
async def test_verification_evaluator():
    evaluator = VerificationEvaluator()
    res = await evaluator.evaluate()
    assert res["sample_count"] > 0
    assert "verification_accuracy" in res["metrics"]


@pytest.mark.asyncio
async def test_rag_evaluator():
    evaluator = RAGEvaluator()
    res = await evaluator.evaluate()
    assert res["sample_count"] > 0
    assert "mean_groundedness_score" in res["metrics"]
    assert "citation_coverage_rate" in res["metrics"]


@pytest.mark.asyncio
async def test_workflow_evaluator():
    evaluator = WorkflowEvaluator()
    res = await evaluator.evaluate()
    assert res["sample_count"] > 0
    assert "success_rate" in res["metrics"]
    assert "human_review_accuracy" in res["metrics"]


# ===========================================================================
# 3. Master Evaluation Runner & Report Generation Test
# ===========================================================================

@pytest.mark.asyncio
async def test_master_evaluation_runner(tmp_path: Path):
    test_report_path = str(tmp_path / "test_report.json")
    report = await run_all_evaluations(
        suites=["complaint", "route", "rag"],
        output_path=test_report_path,
    )

    assert "report_metadata" in report
    assert report["report_metadata"]["paid_apis_called"] is False
    assert report["report_metadata"]["total_suites_executed"] == 3
    assert Path(test_report_path).exists()

    with open(test_report_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["report_metadata"]["jurisdiction"] == "Kalady Grama Panchayat, Kerala"
