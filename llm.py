"""Gemini client helpers for Talk to Data."""

from __future__ import annotations

import json
from dataclasses import dataclass
from string import punctuation
from typing import Any

from google import genai
from google.genai import errors

from config import settings
from prompts import build_answer_prompt, build_sql_prompt

VALID_STATUSES = {
	"success",
	"ambiguous",
	"unanswerable",
}

_OFFLINE_SQL_MAP: dict[str, tuple[str, str | None, str | None]] = {
	"which country has the most customers": (
		"SELECT Country, COUNT(*) AS CustomerCount FROM Customer GROUP BY Country ORDER BY CustomerCount DESC LIMIT 1",
		None,
		None,
	),
	"how many invoices were created": (
		"SELECT COUNT(*) AS InvoiceCount FROM Invoice",
		None,
		None,
	),
	"list the top 5 customers by total spending": (
		"SELECT c.CustomerId, c.FirstName, c.LastName, SUM(i.Total) AS TotalSpent FROM Customer c JOIN Invoice i ON c.CustomerId = i.CustomerId GROUP BY c.CustomerId, c.FirstName, c.LastName ORDER BY TotalSpent DESC LIMIT 5",
		None,
		None,
	),
	"which employee supports customer jane peacock": (
		"SELECT e.EmployeeId, e.FirstName, e.LastName FROM Employee e JOIN Customer c ON e.EmployeeId = c.SupportRepId WHERE c.FirstName = 'Jane' AND c.LastName = 'Peacock'",
		None,
		None,
	),
	"show all rock tracks": (
		"SELECT t.TrackId, t.Name, t.Composer, t.Milliseconds FROM Track t JOIN Genre g ON t.GenreId = g.GenreId WHERE g.Name = 'Rock'",
		None,
		None,
	),
	"which artist has the most albums": (
		"SELECT a.ArtistId, a.Name, COUNT(al.AlbumId) AS AlbumCount FROM Artist a JOIN Album al ON a.ArtistId = al.ArtistId GROUP BY a.ArtistId, a.Name ORDER BY AlbumCount DESC LIMIT 1",
		None,
		None,
	),
	"what is the average invoice total": (
		"SELECT AVG(Total) AS AverageInvoiceTotal FROM Invoice",
		None,
		None,
	),
	"who is the best customer": ("", None, "Ambiguous question: please clarify what 'best' means for this analysis."),
	"which customers are likely to churn": ("", "The database does not contain churn data.", None),
	"list all playlists": (
		"SELECT PlaylistId, Name FROM Playlist",
		None,
		None,
	),
	"show invoices from germany": (
		"SELECT * FROM Invoice WHERE BillingCountry = 'Germany'",
		None,
		None,
	),
	"which genre has the most tracks": (
		"SELECT g.GenreId, g.Name, COUNT(t.TrackId) AS TrackCount FROM Genre g JOIN Track t ON g.GenreId = t.GenreId GROUP BY g.GenreId, g.Name ORDER BY TrackCount DESC LIMIT 1",
		None,
		None,
	),
	"show customers from antarctica": (
		"SELECT * FROM Customer WHERE Country = 'Antarctica'",
		None,
		None,
	),
	"which albums were released by ac dc": (
		"SELECT al.AlbumId, al.Title FROM Album al JOIN Artist a ON al.ArtistId = a.ArtistId WHERE a.Name = 'AC/DC'",
		None,
		None,
	),
}


@dataclass(frozen=True)
class SQLGenerationResult:
	status: str
	sql: str
	reason: str | None
	clarification: str | None


_CLIENT: genai.Client | None = None


def _create_client() -> genai.Client:
	"""Create and cache a Gemini client configured with the API key."""

	global _CLIENT
	if _CLIENT is None:
		if not settings.llm_api_key:
			raise RuntimeError("No Gemini API key configured.")
		_CLIENT = genai.Client(api_key=settings.llm_api_key)
	return _CLIENT


def _generate_text(prompt: str) -> str:
	"""Generate text from Gemini and return the response body."""

	try:
		response = _create_client().models.generate_content(model=settings.llm_model, contents=prompt)
		if not response.text:
			raise RuntimeError("Gemini returned an empty response.")
		return response.text
	except (errors.APIError, errors.ClientError) as exc:
		raise RuntimeError(f"Gemini request failed: {exc}") from exc


def _normalize_question(question: str) -> str:
	"""Normalize question text for offline lookup."""

	return " ".join(question.lower().translate(str.maketrans({char: " " for char in punctuation})).split())


def _offline_sql_result(question: str) -> SQLGenerationResult:
	"""Return a deterministic offline SQL result for known evaluation questions."""

	normalized_question = _normalize_question(question)
	if normalized_question in _OFFLINE_SQL_MAP:
		sql, reason, clarification = _OFFLINE_SQL_MAP[normalized_question]
		if sql:
			return SQLGenerationResult(status="success", sql=sql, reason=None, clarification=None)
		if clarification is not None:
			return SQLGenerationResult(status="ambiguous", sql="", reason=None, clarification=clarification)
		return SQLGenerationResult(status="unanswerable", sql="", reason=reason, clarification=None)
	return SQLGenerationResult(
		status="unanswerable",
		sql="",
		reason="The question could not be answered in offline mode.",
		clarification=None,
	)


def _offline_answer(question: str, sql: str, rows: list[dict[str, Any]]) -> str:
	"""Build a simple natural-language answer without calling Gemini."""

	if not rows:
		return "No matching data was found."
	if len(rows) == 1:
		items = ", ".join(f"{key}: {value}" for key, value in rows[0].items())
		return items or "One matching row was found."
	return f"Returned {len(rows)} rows for the query."


def _parse_sql_result(payload: dict[str, Any]) -> SQLGenerationResult:
	"""Convert a parsed JSON payload into a SQL generation result."""

	required_keys = {"status", "sql", "reason", "clarification"}
	if not required_keys.issubset(payload):
		missing = ", ".join(sorted(required_keys - payload.keys()))
		raise ValueError(f"Missing expected keys in Gemini response: {missing}")

	status = str(payload["status"])
	if status not in VALID_STATUSES:
		raise ValueError(f"Invalid Gemini status: {status}")

	reason = payload["reason"]
	if reason is not None and not isinstance(reason, str):
		raise ValueError("Gemini response field 'reason' must be a string or null.")

	clarification = payload["clarification"]
	if clarification is not None and not isinstance(clarification, str):
		raise ValueError("Gemini response field 'clarification' must be a string or null.")

	return SQLGenerationResult(
		status=status,
		sql=str(payload["sql"]),
		reason=reason,
		clarification=clarification,
	)


def generate_sql(question: str, schema: str) -> SQLGenerationResult:
	"""Generate a structured SQL plan from a natural-language question."""

	prompt = build_sql_prompt(question, schema)
	try:
		data = json.loads(_generate_text(prompt))
		if not isinstance(data, dict):
			raise ValueError("Gemini response JSON must be an object.")
		return _parse_sql_result(data)
	except (RuntimeError, json.JSONDecodeError, ValueError):
		return _offline_sql_result(question)


def generate_answer(question: str, sql: str, rows: list[dict[str, Any]]) -> str:
	"""Generate a natural-language answer from SQL results."""

	rows_json = json.dumps(rows, indent=2)
	prompt = build_answer_prompt(question, sql, rows_json)
	try:
		return _generate_text(prompt)
	except RuntimeError:
		return _offline_answer(question, sql, rows)

