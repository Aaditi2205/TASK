"""FastAPI entry point for Talk to Data."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from pipeline import process_question

app = FastAPI(
	title="Talk to Data API",
	description="Conversational analytics service for SQLite databases.",
	version="1.0.0",
)


class QuestionRequest(BaseModel):
	"""Incoming question payload."""

	question: str = Field(min_length=1)


class QuestionResponse(BaseModel):
	"""Response payload returned by the API."""

	status: str
	answer: str | None
	sql: str | None
	rows: list[dict]
	reason: str | None
	clarification: str | None


@app.get("/")
def health() -> dict[str, str]:
	"""Return a simple health response."""

	return {"status": "healthy", "service": "Talk to Data API"}


@app.post("/ask", response_model=QuestionResponse)
def ask(request: QuestionRequest) -> QuestionResponse:
	"""Process a question through the pipeline and return the structured result."""

	result = process_question(request.question)
	if result.status == "error":
		raise HTTPException(status_code=400, detail=result.reason)
	return QuestionResponse(**result.__dict__)

