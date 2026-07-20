# Talk to Data Written Component

## 7a. AI Usage Log

- I used AI tools to scaffold the project structure, draft module boundaries, and speed up repetitive code like prompt templates, dataclasses, tests, and README formatting.
- I used AI to debug environment issues such as `.env` loading, Git setup, and the Gemini API error path.
- I rejected or fixed a few AI suggestions:
  - A first pass used a raw dictionary for validation results; I changed it to a frozen dataclass for clearer structure.
  - I initially had `.env.example` contain a real API key; I replaced it with a placeholder and moved the real key to `.env`.
  - I added an offline fallback in `llm.py` after Gemini quota issues blocked live runs. That was a pragmatic workaround for demoability, not the ideal production path.
- I am comfortable explaining the overall architecture and most of the implementation. The only part I would flag as a temporary compromise is the offline fallback in `llm.py`, because it exists to keep the project runnable when Gemini quota is unavailable.

## 7b. Key Decisions

### 1. Keep `pipeline.py` as the orchestrator
- Decision: Put the end-to-end workflow in `pipeline.py` and keep the other modules focused on one job each.
- Alternatives: Put more logic in `app.py` or split the workflow across the API and helpers.
- Why: This keeps the system easy to reason about, test, and explain.

### 2. Validate SQL before execution
- Decision: Use `validator.py` as a guardrail before the database ever sees generated SQL.
- Alternatives: Trust the LLM output directly, or rely only on read-only database access.
- Why: Validation catches bad or unsafe SQL early, and read-only mode is only the last layer of defense.

### 3. Separate prompt construction from Gemini calls
- Decision: Keep prompts in `prompts.py` and Gemini communication in `llm.py`.
- Alternatives: Build prompt strings inline in the LLM wrapper.
- Why: Prompt wording can change without touching API code, and the module boundaries stay clean.

### 4. Return structured results instead of free-form values
- Decision: Use dataclasses like `PipelineResult`, `SQLGenerationResult`, and `EvaluationResult`.
- Alternatives: Return tuples or dictionaries everywhere.
- Why: Named fields are easier to understand, safer to refactor, and clearer in tests.

### 5. Add an evaluation harness from day one
- Decision: Build `eval.py` and a labeled `cases.yaml` benchmark.
- Alternatives: Rely only on manual testing.
- Why: It gives a repeatable way to measure correctness and spot failure modes honestly.

## 7c. Design Questions

### 1. Top ways the system could produce a wrong but confident-looking answer
- The LLM could generate a plausible but incorrect SQL query. I would catch this by inspecting the SQL and comparing it to the expected tables and joins.
- The SQL could be valid but return misleading rows because of a subtle join or aggregation mistake. I would catch this with benchmark cases and manual spot checks on representative questions.
- The answer generator could overstate what the rows show. I would catch this by forcing the final answer to stay grounded in the returned rows and by checking that the raw rows are visible in evaluation.

### 2. If the dataset were much larger
- I would not send the full schema every time. I would retrieve only the relevant tables/columns for the question, then build a smaller prompt from that subset.

### Optional bonus: if the same question returned different answers
- I would compare the exact prompt, model settings, generated SQL, and returned rows for each run.
- I would also check for non-determinism from the model, a changed schema, or a different runtime environment.

## 7d. Code Critique

The snippet is flawed in several ways:

- It blindly sends the entire schema to the model, which wastes context and can confuse the LLM.
- It executes whatever SQL the model returns, which is unsafe and allows writes or destructive statements.
- It has no validation layer, so there is no protection against `DELETE`, `DROP`, or multiple statements.
- It does not enforce read-only access or a row limit.
- It asks the LLM to answer from raw rows without a clear contract, so the final answer may drift from the data.
- It has no handling for ambiguous or unanswerable questions.
- It provides no evaluation or traceability beyond the final answer, so it is hard to trust or debug.
- It mixes orchestration, database access, and LLM behavior into one function, which makes the code hard to test and maintain.

## Notes

- The current submission is designed as a small, readable system with a strict separation of concerns.
- The benchmark and tests focus on the most important failure modes: unsafe SQL, ambiguity, and unsupported questions.
