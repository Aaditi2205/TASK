"""Prompt templates for Talk to Data."""

from __future__ import annotations

from textwrap import dedent


def build_sql_prompt(question: str, schema: str) -> str:
	"""Build the prompt used to generate SQL from a user question."""

	return dedent(
		f"""
		You are an expert SQL assistant.
		You are working with a SQLite database.
		Use ONLY the provided schema.
		Never invent tables or columns.
		If the question is ambiguous, do not guess.
		Return ONLY valid JSON.
		The response must be valid JSON that can be parsed directly using Python's json.loads().
		Do not include markdown.
		Do not explain your reasoning.

		Required JSON format:
		{{
		  "status": "success" | "ambiguous" | "unanswerable",
		  "sql": "...",
		  "reason": "...",
		  "clarification": "..."
		}}

		Rules:
		- "success": sql contains a SELECT query. reason and clarification may be null.
		- "ambiguous": sql must be an empty string. clarification should ask what information is missing.
		- "unanswerable": sql must be an empty string. reason explains why the database cannot answer.

		Schema:
		{schema}

		Question:
		{question}
		"""
	).strip()


def build_answer_prompt(question: str, sql: str, rows: str) -> str:
	"""Build the prompt used to turn SQL results into a natural-language answer."""

	return dedent(
		f"""
		Answer ONLY using the provided SQL results.
		Never invent facts.
		If the rows are empty, clearly say no matching data was found.
		If multiple rows are returned, summarize them clearly without inventing information.
		Do not mention internal implementation.
		Keep the answer concise and natural.
		Do not generate SQL.
		Do not use markdown.

		Original question:
		{question}

		Executed SQL:
		{sql}

		Query results:
		{rows}
		"""
	).strip()

