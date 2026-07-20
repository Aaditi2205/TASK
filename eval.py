"""Evaluation harness for Talk to Data."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from pipeline import process_question


@dataclass(frozen=True)
class EvaluationResult:
	case_id: str
	description: str
	question: str
	expected_status: str
	actual_status: str
	passed: bool


def load_cases(path: str = "cases.yaml") -> list[dict]:
	"""Load evaluation cases from a YAML file."""

	try:
		with Path(path).open("r", encoding="utf-8") as file:
			data = yaml.safe_load(file) or {}
	except (OSError, yaml.YAMLError) as exc:
		raise RuntimeError(f"Failed to load evaluation cases from {path}: {exc}") from exc
	return list(data.get("cases", []))


def run_evaluation(path: str = "cases.yaml") -> list[EvaluationResult]:
	"""Run the pipeline against all evaluation cases."""

	results: list[EvaluationResult] = []
	for case in load_cases(path):
		result = process_question(case["question"])
		results.append(
			EvaluationResult(
				case_id=case["id"],
				description=case["description"],
				question=case["question"],
				expected_status=case["expected_status"],
				actual_status=result.status,
				passed=result.status == case["expected_status"],
			)
		)
	return results


def print_summary(results: list[EvaluationResult]) -> None:
	"""Print a simple pass/fail summary for evaluation results."""

	print("========================================")
	print("Talk to Data Evaluation")
	print("========================================")
	print()
	for result in results:
		print(f"{'PASS' if result.passed else 'FAIL'}  {result.case_id}")
	print()
	print("----------------------------------------")
	print()
	passed = sum(result.passed for result in results)
	failed = len(results) - passed
	accuracy = (passed / len(results) * 100) if results else 0.0
	print("Summary")
	print()
	print(f"Passed : {passed}")
	print(f"Failed : {failed}")
	print(f"Accuracy : {accuracy:.2f}%")


if __name__ == "__main__":
	results = run_evaluation()
	print_summary(results)

