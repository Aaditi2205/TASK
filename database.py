"""SQLite access helpers for Talk to Data.

This module only handles database connectivity and query execution.
It does not validate SQL, generate prompts, or talk to any LLM.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from config import settings


def create_connection() -> sqlite3.Connection:
	"""Create a read-only SQLite connection to the configured database."""

	database_path = Path(settings.database_path).resolve()
	if not database_path.exists():
		raise FileNotFoundError(f"Database file not found: {database_path}")

	database_uri = database_path.as_uri() + "?mode=ro"

	try:
		return sqlite3.connect(
			database_uri,
			uri=True,
			timeout=settings.query_timeout,
		)
	except sqlite3.Error as exc:
		raise RuntimeError(f"Failed to open database connection: {exc}") from exc


def execute_select_query(query: str, parameters: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
	"""Execute a validated SQL SELECT query and return rows as dictionaries."""

	with closing(create_connection()) as connection:
		with closing(connection.cursor()) as cursor:
			try:
				if parameters is None:
					cursor.execute(query)
				else:
					cursor.execute(query, parameters)

				columns = [column[0] for column in cursor.description or ()]
				return [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]
			except sqlite3.Error as exc:
				raise RuntimeError(f"Failed to execute query: {exc}") from exc

