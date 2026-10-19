"""
SwachhLoop AI — Master AI Evaluation Suite Runner
=================================================
Phase 5: Reproducible offline evaluation suite for all AI services & agent workflows.

Usage:
  python -m evaluations.runner
  python -m evaluations.runner --output evaluations/reports/custom_report.json
  python -m evaluations.runner --suite complaint,rag
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Any

from evaluations.evaluators.complaint_evaluator import ComplaintEvaluator
from evaluations.evaluators.waste_evaluator import WasteDetectionEvaluator
from evaluations.evaluators.route_evaluator import RouteEvaluator
from evaluations.evaluators.verification_evaluator import VerificationEvaluator
from evaluations.evaluators.rag_evaluator import RAGEvaluator
from evaluations.evaluators.workflow_evaluator import WorkflowEvaluator

METRIC_DEFINITIONS = {
    "urgency_accuracy": "Proportion of citizen complaints where assessed urgency matches ground truth exactly.",
    "urgency_macro_f1": "Harmonic mean of precision and recall across all urgency classes with equal weighting.",
    "location_extraction_accuracy": "Accuracy of extracting correct Kalady landmark or recognizing missing location.",
    "ambiguity_detection_accuracy": "Accuracy of identifying vague descriptions or missing location tags.",
    "detection_accuracy": "Proportion of image fixtures where waste presence was correctly identified.",
    "category_accuracy": "Accuracy of assigning the dominant waste category (plastic/organic).",
    "bounding_box_validity_rate": "Percentage of generated bounding boxes adhering to coordinate and dimension bounds.",
    "constraint_violation_rate": "Fraction of computed routes that violate physical bounds or lose stops.",
    "average_distance_reduction_pct": "Percentage of travel distance saved by TSP compared to naive stop traversal.",
    "verification_accuracy": "Accuracy across verified clean, partially clean, and failed/identical cleanup verdicts.",
    "mean_relevance_score": "Average BM25 token relevance score of retrieved civic knowledge articles.",
    "mean_groundedness_score": "Average lexical overlap ratio between generated RAG answers and retrieved context.",
    "citation_coverage_rate": "Percentage of in-domain civic queries retrieving the correct official knowledge article.",
    "fallback_accuracy": "Percentage of out-of-domain or adversarial queries correctly marked as insufficient-context.",
    "success_rate": "Percentage of multi-agent LangGraph workflows completing without unhandled exceptions.",
    "human_review_accuracy": "Accuracy of triggering human supervisor gates on high-risk hazards or uncertain verdicts.",
    "mean_latency_ms": "Average execution duration per multi-agent workflow in milliseconds.",
}


async def run_all_evaluations(
    suites: list[str] | None = None,
    output_path: str = "evaluations/reports/evaluation_report.json",
) -> dict[str, Any]:
    evaluators_map = {
        "complaint": ComplaintEvaluator(),
        "waste": WasteDetectionEvaluator(),
        "route": RouteEvaluator(),
        "verification": VerificationEvaluator(),
        "rag": RAGEvaluator(),
        "workflow": WorkflowEvaluator(),
    }

    selected_keys = suites if suites else list(evaluators_map.keys())

    print("=" * 70)
    print(" SWACHHLOOP AI — PHASE 5 OFFLINE AI EVALUATION SUITE")
    print(" Focus Area: Kalady Grama Panchayat, Kerala")
    print(f" Execution Time: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 70)

    start_time = time.perf_counter()
    suite_results: dict[str, Any] = {}
    total_samples = 0

    for key in selected_keys:
        if key not in evaluators_map:
            print(f"[!] Warning: Unknown suite '{key}'. Skipping.")
            continue

        evaluator = evaluators_map[key]
        print(f"\n[+] Running {evaluator.name}...")
        try:
            res = await evaluator.evaluate()
            suite_results[key] = res
            samples = res.get("sample_count", 0)
            total_samples += samples
            print(f"    Completed: {samples} samples evaluated.")
            metrics = res.get("metrics", {})
            for m_name, m_val in metrics.items():
                if isinstance(m_val, float):
                    print(f"      - {m_name}: {m_val:.4f}")
                else:
                    print(f"      - {m_name}: {m_val}")
        except Exception as err:
            print(f"    [!] Failed to execute suite '{key}': {err}")
            suite_results[key] = {"error": str(err), "status": "FAILED"}

    total_duration_s = round(time.perf_counter() - start_time, 3)

    report: dict[str, Any] = {
        "report_metadata": {
            "title": "SwachhLoop AI — Phase 5 Offline AI Evaluation Report",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "target_system": "SwachhLoop AI (SwachhNavigator)",
            "jurisdiction": "Kalady Grama Panchayat, Kerala",
            "evaluation_mode": "deterministic_offline_fixtures",
            "paid_apis_called": False,
            "total_suites_executed": len(suite_results),
            "total_test_samples": total_samples,
            "total_duration_seconds": total_duration_s,
        },
        "metric_definitions": METRIC_DEFINITIONS,
        "suites": suite_results,
    }

    # Save to disk
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print(f" [OK] Evaluation completed in {total_duration_s}s.")
    print(f" [OK] Machine-readable report saved to: {out_file.resolve()}")
    print("=" * 70)

    return report


def main():
    parser = argparse.ArgumentParser(description="SwachhLoop AI Evaluation Suite Runner")
    parser.add_argument(
        "--output",
        default="evaluations/reports/evaluation_report.json",
        help="Path to save JSON evaluation report",
    )
    parser.add_argument(
        "--suite",
        default=None,
        help="Comma-separated list of suites to run (e.g. complaint,waste,route,verification,rag,workflow)",
    )
    args = parser.parse_args()

    suites = [s.strip() for s in args.suite.split(",")] if args.suite else None
    asyncio.run(run_all_evaluations(suites=suites, output_path=args.output))


if __name__ == "__main__":
    main()
