"""Pytest suite for Talk to Data."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from llm import SQLGenerationResult
from pipeline import PipelineResult, process_question
from validator import ValidationResult, validate_sql


@pytest.mark.parametrize(
	"query, expected_valid, expected_sql, expected_reason",
	[
		("SELECT * FROM Customer", True, "SELECT * FROM Customer LIMIT 100", None),
		("INSERT INTO Customer VALUES (1)", False, "", "Only SELECT queries are allowed."),
		("UPDATE Customer SET FirstName = 'A'", False, "", "Only SELECT queries are allowed."),
		("DELETE FROM Customer", False, "", "Only SELECT queries are allowed."),
		("DROP TABLE Customer", False, "", "Only SELECT queries are allowed."),
		("ALTER TABLE Customer ADD COLUMN X TEXT", False, "", "Only SELECT queries are allowed."),
		("SELECT * FROM Customer; DROP TABLE Customer;", False, "", "Multiple SQL statements are not allowed."),
	],
)
def test_validate_sql_rules(query: str, expected_valid: bool, expected_sql: str, expected_reason: str | None) -> None:
	result = validate_sql(query)
	assert result.valid is expected_valid
	assert result.sql == expected_sql
	assert result.reason == expected_reason


def test_validate_sql_preserves_existing_limit() -> None:
	result = validate_sql("SELECT * FROM Customer LIMIT 5")
	assert result == ValidationResult(valid=True, sql="SELECT * FROM Customer LIMIT 5", reason=None)


@patch("pipeline.generate_answer")
@patch("pipeline.execute_select_query")
@patch("pipeline.validate_sql")
@patch("pipeline.generate_sql")
@patch("pipeline.get_schema_description")
def test_process_question_success(mock_schema, mock_generate_sql, mock_validate_sql, mock_execute, mock_answer) -> None:
	mock_schema.return_value = "Table: Customer"
	mock_generate_sql.return_value = SQLGenerationResult("success", "SELECT * FROM Customer", None, None)
	mock_validate_sql.return_value = ValidationResult(True, "SELECT * FROM Customer LIMIT 100", None)
	mock_execute.return_value = [{"CustomerId": 1}]
	mock_answer.return_value = "There is 1 customer."

	result = process_question("How many customers are there?")

	assert result == PipelineResult("success", "There is 1 customer.", "SELECT * FROM Customer LIMIT 100", [{"CustomerId": 1}], None, None)
	mock_answer.assert_called_once()


@patch("pipeline.generate_sql")
@patch("pipeline.get_schema_description")
def test_process_question_ambiguous(mock_schema, mock_generate_sql) -> None:
	mock_schema.return_value = "Table: Customer"
	mock_generate_sql.return_value = SQLGenerationResult("ambiguous", "", None, "Which customer field do you mean?")

	result = process_question("Who is the best customer?")

	assert result.status == "ambiguous"
	assert result.answer is None
	assert result.sql is None
	assert result.clarification == "Which customer field do you mean?"


@patch("pipeline.generate_sql")
@patch("pipeline.get_schema_description")
def test_process_question_unanswerable(mock_schema, mock_generate_sql) -> None:
	mock_schema.return_value = "Table: Customer"
	mock_generate_sql.return_value = SQLGenerationResult("unanswerable", "", "The database has no churn data.", None)

	result = process_question("Which customers are likely to churn?")

	assert result.status == "unanswerable"
	assert result.answer is None
	assert result.sql is None
	assert result.reason == "The database has no churn data."


@patch("pipeline.validate_sql")
@patch("pipeline.generate_sql")
@patch("pipeline.get_schema_description")
def test_process_question_invalid_sql(mock_schema, mock_generate_sql, mock_validate_sql) -> None:
	mock_schema.return_value = "Table: Customer"
	mock_generate_sql.return_value = SQLGenerationResult("success", "DELETE FROM Customer", None, None)
	mock_validate_sql.return_value = ValidationResult(False, "", "Only SELECT queries are allowed.")

	result = process_question("Remove a customer")

	assert result.status == "error"
	assert result.answer is None
	assert result.sql is None
	assert result.reason == "Only SELECT queries are allowed."


@patch("pipeline.execute_select_query")
@patch("pipeline.validate_sql")
@patch("pipeline.generate_sql")
@patch("pipeline.get_schema_description")
def test_process_question_database_error(mock_schema, mock_generate_sql, mock_validate_sql, mock_execute) -> None:
	mock_schema.return_value = "Table: Customer"
	mock_generate_sql.return_value = SQLGenerationResult("success", "SELECT * FROM Customer", None, None)
	mock_validate_sql.return_value = ValidationResult(True, "SELECT * FROM Customer LIMIT 100", None)
	mock_execute.side_effect = RuntimeError("database unavailable")

	result = process_question("Show all customers")

	assert result.status == "error"
	assert result.answer is None
	assert result.sql is None
	assert result.reason == "database unavailable"

