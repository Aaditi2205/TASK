"""Workflow orchestration for Talk to Data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from database import execute_select_query
from llm import generate_answer, generate_sql
from schema import get_schema_description
from validator import validate_sql


@dataclass(frozen=True)
class PipelineResult:
	status: str
	answer: str | None
	sql: str | None
	rows: list[dict[str, Any]]
	reason: str | None
	clarification: str | None


def _success(answer: str, sql: str, rows: list[dict[str, Any]]) -> PipelineResult:
	return PipelineResult(status="success", answer=answer, sql=sql, rows=rows, reason=None, clarification=None)


def _error(reason: str) -> PipelineResult:
	return PipelineResult(status="error", answer=None, sql=None, rows=[], reason=reason, clarification=None)


def _ambiguous(clarification: str | None) -> PipelineResult:
	return PipelineResult(status="ambiguous", answer=None, sql=None, rows=[], reason=None, clarification=clarification)


def _unanswerable(reason: str | None) -> PipelineResult:
	return PipelineResult(status="unanswerable", answer=None, sql=None, rows=[], reason=reason, clarification=None)


def process_question(question: str) -> PipelineResult:
	"""Process a user question through schema lookup, SQL generation, validation, and answering."""

	try:
		schema = get_schema_description()
		sql_result = generate_sql(question, schema)

		if sql_result.status == "ambiguous":
			return _ambiguous(sql_result.clarification)

		if sql_result.status == "unanswerable":
			return _unanswerable(sql_result.reason)

		if sql_result.status != "success":
			raise RuntimeError(f"Unexpected SQL generation status: {sql_result.status}")

		validation_result = validate_sql(sql_result.sql)
		if not validation_result.valid:
			return _error(validation_result.reason or "SQL validation failed.")

		rows = execute_select_query(validation_result.sql)
		answer = generate_answer(question, validation_result.sql, rows)
		return _success(answer, validation_result.sql, rows)
	except Exception as exc:
		return _error(str(exc))

