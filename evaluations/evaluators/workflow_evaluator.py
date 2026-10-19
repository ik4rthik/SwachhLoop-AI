"""
SwachhLoop AI — LangGraph Multi-Agent Workflow Evaluator
=======================================================
Evaluates multi-agent orchestration completion rates, review gate decisions,
error handling on unknown tasks, and latency.
"""

import json
from pathlib import Path
import time
from typing import Any

from backend.agents.orchestrator import run_swachhloop_workflow
from evaluations.evaluators.base import BaseEvaluator
from evaluations.metrics import compute_workflow_evaluation_metrics


class WorkflowEvaluator(BaseEvaluator):
    def __init__(self, dataset_path: str = "evaluations/datasets/workflows_eval.json"):
        self.dataset_path = Path(dataset_path)

    @property
    def name(self) -> str:
        return "LangGraph Multi-Agent Orchestration & Governance Evaluation"

    async def evaluate(self) -> dict[str, Any]:
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Evaluation dataset not found at {self.dataset_path}")

        with open(self.dataset_path, "r", encoding="utf-8") as f:
            cases = json.load(f)

        records: list[dict[str, Any]] = []

        for case in cases:
            task_type = case["task_type"]
            payload = case.get("payload", {})
            expected_status = case["expected_status"]
            expected_review = case["expected_human_review"]

            t0 = time.perf_counter()
            try:
                state = await run_swachhloop_workflow(
                    task_type=task_type,
                    **payload,
                )
                t_elapsed_ms = (time.perf_counter() - t0) * 1000.0

                actual_status = state.get("status")
                actual_review = state.get("requires_human_review", False)

                records.append({
                    "id": case["id"],
                    "name": case["name"],
                    "task_type": task_type,
                    "status": actual_status,
                    "expected_status": expected_status,
                    "status_match": actual_status == expected_status,
                    "requires_human_review": actual_review,
                    "expected_human_review": expected_review,
                    "review_match": actual_review == expected_review,
                    "latency_ms": round(t_elapsed_ms, 2),
                    "audit_step_count": len(state.get("audit_trail", [])),
                })
            except Exception as err:
                t_elapsed_ms = (time.perf_counter() - t0) * 1000.0
                records.append({
                    "id": case["id"],
                    "name": case["name"],
                    "task_type": task_type,
                    "status": "EXCEPTION",
                    "expected_status": expected_status,
                    "status_match": False,
                    "requires_human_review": True,
                    "expected_human_review": expected_review,
                    "review_match": False,
                    "latency_ms": round(t_elapsed_ms, 2),
                    "error": str(err),
                })

        metrics = compute_workflow_evaluation_metrics(records)

        return {
            "suite_name": self.name,
            "dataset_type": "offline_synthetic_fixtures",
            "sample_count": len(cases),
            "metrics": metrics,
            "details": records,
        }
