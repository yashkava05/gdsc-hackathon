We are building a command-line Python utility called `triage`. This task ONLY sets up the project and creates the data schema. Do not build any other part of the project.

Create exactly these, and nothing else:
1. A file `requirements.txt`
2. A file `schema.py`
3. An empty directory `samples/`

Do not create, modify, or stub any other files.

requirements.txt — contents are exactly two dependencies, one per line:
  pydantic>=2
  requests
Add no other dependencies.

schema.py — Pydantic v2 only. Define exactly the following, with no additional classes, fields, methods, validators, or config:

- `Severity`: a class inheriting from both `str` and `enum.Enum`, with exactly these four members and string values:
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"

- `LogEvent(BaseModel)`: with exactly these fields, in this order, with these exact types:
    service_name: str
    timestamp: str
    error_severity: Severity
    suggested_remediation: str
    source_line: int
    confidence: str
    schema_version: str = "1.0"

Constraints:
- No web frameworks (no Flask, FastAPI, Streamlit, Django, etc.).
- No AI APIs or AI SDKs imported anywhere (no Gemini, OpenAI, Anthropic, etc.).
- No dependencies beyond pydantic>=2 and requests.
- No files beyond requirements.txt, schema.py, and the samples/ directory.
- No placeholder code, no TODO comments, no commented-out code.
- Pydantic v2 syntax only (e.g. model_dump_json, not the v1 .json()).

Done when: `from schema import LogEvent, Severity` succeeds, a fully-populated LogEvent validates, and passing an invalid error_severity raises a Pydantic ValidationError.
