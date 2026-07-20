"""SQLite schema inspection helpers for Talk to Data."""

from __future__ import annotations

import sqlite3
from contextlib import closing

from database import create_connection


def get_table_names() -> list[str]:
	"""Return user table names sorted alphabetically."""

	query = (
		"SELECT name "
		"FROM sqlite_master "
		"WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
		"ORDER BY name ASC"
	)

	try:
		with create_connection() as connection:
			with closing(connection.cursor()) as cursor:
				cursor.execute(query)
				return [row[0] for row in cursor.fetchall()]
	except sqlite3.Error as exc:
		raise RuntimeError(f"Failed to read table names: {exc}") from exc


def get_schema_description() -> str:
	"""Return a readable description of all user tables and columns."""

	try:
		table_names = get_table_names()
		descriptions: list[str] = []

		with create_connection() as connection:
			for table_name in table_names:
				# Table names come from sqlite_master, not from user input.
				with closing(connection.cursor()) as cursor:
					cursor.execute(f"PRAGMA table_info('{table_name}')")
					columns = cursor.fetchall()
					descriptions.append(f"Table: {table_name}")
					for _, column_name, column_type, *_ in columns:
						descriptions.append(f"- {column_name} ({column_type or 'UNKNOWN'})")
					descriptions.append("")

		return "\n".join(descriptions).rstrip()
	except sqlite3.Error as exc:
		raise RuntimeError(f"Failed to read schema description: {exc}") from exc

