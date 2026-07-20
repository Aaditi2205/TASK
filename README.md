<<<<<<< HEAD
# TASK
=======
﻿# Talk to Data

Talk to Data is a conversational analytics application that converts natural language questions into safe SQL queries over a SQLite database using an LLM. The generated SQL is validated before execution, the results are fetched from the database in read-only mode, and the final response is returned as a natural-language answer.

---

## Features

- Natural language to SQL
- Read-only SQLite database
- SQL validation layer
- Protection against non-SELECT queries
- Automatic LIMIT enforcement
- Ambiguous question handling
- Unanswerable question handling
- FastAPI REST API
- Evaluation harness
- Unit tests

---

## Project Structure

```text
talk-to-data/
├── app.py
├── config.py
├── database.py
├── schema.py
├── validator.py
├── prompts.py
├── llm.py
├── pipeline.py
├── eval.py
├── tests.py
├── cases.yaml
├── README.md
├── requirements.txt
└── data/
	└── Chinook.db
```

---

## Architecture

```text
User
│
▼
FastAPI
│
▼
Pipeline
├── Schema Reader
├── LLM
├── SQL Validator
├── Database
└── LLM Answer Generator
```

`pipeline.py` orchestrates the full workflow, while each supporting module has a single responsibility. This keeps the system easy to test, explain, and maintain.

---

## Workflow

1. Receive user question.
2. Read database schema.
3. Ask the LLM to generate SQL.
4. Validate the generated SQL.
5. Execute the SQL.
6. Ask the LLM to summarize the results.
7. Return the response.

---

## Installation

```bash
git clone <repository>
cd talk-to-data
python -m venv .venv
```

Activate the virtual environment:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file with your local configuration. The project reads these values:

```env
GEMINI_API_KEY=your_api_key
LLM_MODEL=gemini-2.0-flash
DATABASE_PATH=data/Chinook.db
```

---

## Running the API

Start the FastAPI server with:

```bash
uvicorn app:app --reload
```

Swagger UI is available at:

```text
http://127.0.0.1:8000/docs
```

---

## Running Evaluation

```bash
python eval.py
```

This runs all cases from `cases.yaml` and prints pass/fail statistics for the pipeline.

---

## Running Tests

```bash
pytest
```

---

## Design Decisions

- Single Responsibility Principle keeps each module focused and easy to reason about.
- Read-only database access adds a defense-in-depth layer around SQL execution.
- SQL validation happens before execution to block unsafe or unsupported queries.
- Prompt construction is separated from LLM communication so prompt wording can change independently.
- `pipeline.py` owns orchestration and keeps the end-to-end flow in one place.
- Dataclasses provide lightweight, structured communication between modules.
- Pydantic models provide request and response validation in the API layer.

---

## Assumptions

- The SQLite database already exists.
- The LLM follows the required JSON output format.
- The database schema is relatively stable.
- Only `SELECT` queries are supported.

---

## Future Improvements

- SQL parser instead of regex validation
- Schema caching
- Query result caching
- Authentication
- Conversation memory
- Support for multiple database engines
- Streaming responses

---

## Tech Stack

- Python
- FastAPI
- SQLite
- Pydantic
- PyYAML
- Google Gemini
- Pytest

---

## License

This project is intended for educational purposes as part of an internship assignment.

>>>>>>> origin/master
