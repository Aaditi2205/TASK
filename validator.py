"""SQL validation helpers for Talk to Data."""

from __future__ import annotations

from dataclasses import dataclass
import re

from config import settings

DANGEROUS_KEYWORDS = (
	"INSERT",
	"UPDATE",
	"DELETE",
	"DROP",
	"ALTER",
	"CREATE",
	"TRUNCATE",
	"REPLACE",
	"ATTACH",
	"DETACH",
	"PRAGMA",
	"VACUUM",
	"BEGIN",
	"COMMIT",
	"ROLLBACK",
)


@dataclass(frozen=True)
class ValidationResult:
	valid: bool
	sql: str
	reason: str | None

_SELECT_RE = re.compile(r"^\s*select\b", re.IGNORECASE)
_LIMIT_RE = re.compile(r"\blimit\b", re.IGNORECASE)
_DANGEROUS_RE = re.compile(
	r"\b(?:" + "|".join(DANGEROUS_KEYWORDS) + r")\b",
	re.IGNORECASE,
)


def _mask_literals_and_comments(sql: str) -> str:
	"""Replace quoted text and comments with spaces so keyword checks stay simple."""

	masked: list[str] = []
	i = 0
	in_single = False
	in_double = False
	in_line_comment = False
	in_block_comment = False

	while i < len(sql):
		char = sql[i]
		next_char = sql[i + 1] if i + 1 < len(sql) else ""

		if in_line_comment:
			masked.append(char if char in "\r\n" else " ")
			if char in "\r\n":
				in_line_comment = False
		elif in_block_comment:
			masked.append(" ")
			if char == "*" and next_char == "/":
				masked.append(" ")
				i += 1
				in_block_comment = False
		elif in_single:
			masked.append(" ")
			if char == "'":
				if next_char == "'":
					masked.append(" ")
					i += 1
				else:
					in_single = False
		elif in_double:
			masked.append(" ")
			if char == '"':
				if next_char == '"':
					masked.append(" ")
					i += 1
				else:
					in_double = False
		else:
			if char == "-" and next_char == "-":
				masked.extend([" ", " "])
				i += 1
				in_line_comment = True
			elif char == "/" and next_char == "*":
				masked.extend([" ", " "])
				i += 1
				in_block_comment = True
			elif char == "'":
				masked.append(" ")
				in_single = True
			elif char == '"':
				masked.append(" ")
				in_double = True
			else:
				masked.append(char)

		i += 1

	return "".join(masked)


def validate_sql(query: str) -> ValidationResult:
	"""Validate a SQL query and append LIMIT when needed."""

	if not query or not query.strip():
		return ValidationResult(valid=False, sql="", reason="Query cannot be empty.")

	stripped_query = query.strip()
	clean_query = _mask_literals_and_comments(stripped_query)

	if not _SELECT_RE.match(clean_query):
		return ValidationResult(valid=False, sql="", reason="Only SELECT queries are allowed.")

	body = clean_query.rstrip(";").strip()
	if ";" in body:
		return ValidationResult(valid=False, sql="", reason="Multiple SQL statements are not allowed.")

	if _DANGEROUS_RE.search(clean_query):
		return ValidationResult(valid=False, sql="", reason="Dangerous SQL keywords are not allowed.")

	sql = stripped_query.rstrip(";").strip()
	if not _LIMIT_RE.search(clean_query):
		sql = f"{sql} LIMIT {settings.max_rows}"

	return ValidationResult(valid=True, sql=sql, reason=None)

