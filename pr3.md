We are building a command-line Python utility called `triage`. These files already exist and must NOT be modified: schema.py (defines LogEvent and Severity), funnel.py. This task creates the AI extraction step plus its prompt constants. Do not build any other part of the project.

Create exactly two files: `prompts.py` and `extract.py`
Do not create, modify, or stub any other files.

The ONLY AI model allowed is Gemma via Ollama. No other AI APIs anywhere (no Gemini, no OpenAI, no Anthropic).

--- prompts.py ---
String constants only. No functions, no logic, no imports beyond standard library if needed.
Define exactly one constant:
    SYSTEM_PROMPT: str
It must instruct the model to act as a log-analysis extractor that outputs ONE raw JSON object and nothing else. The instructions in SYSTEM_PROMPT must require:
  - Output raw JSON only. No markdown code fences, no backticks, no prose, no explanation before or after.
  - The JSON object must contain exactly these keys: service_name (string), timestamp (string), error_severity (one of exactly: INFO, WARN, ERROR, FATAL), suggested_remediation (string), source_line (integer), confidence (string), schema_version (string).
  - error_severity must be exactly one of the four allowed uppercase values.
  - If a value is unknown, use a sensible string (e.g. "unknown") rather than null, and never omit a key.

--- extract.py ---
Imports allowed: standard library (json, etc.), requests, and from schema import LogEvent, Severity, and from prompts import SYSTEM_PROMPT. No other third-party imports.

Ollama call details (use exactly these):
  - HTTP POST to: http://localhost:11434/api/generate
  - JSON body: {"model": "gemma2:2b", "prompt": <prompt string>, "stream": false}
  - The model's text output is in response.json()["response"].
  - Use a request timeout of 120 seconds.

Define exactly one public function with this exact signature:

    def extract_event(line_number: int, line: str) -> LogEvent | dict:

Behavior:
- Build the prompt sent to Ollama by combining SYSTEM_PROMPT with the specific line to analyze, and explicitly tell the model that source_line must equal the integer line_number passed in.
- Helper expectation (you may add private helper functions prefixed with `_`, but no other public names): a private function that performs the POST and returns the raw response text string.
- Parsing: the model output is expected to be raw JSON. Before json.loads, defensively strip surrounding whitespace and, if present, strip a leading/trailing markdown code fence (```json ... ```), since small models sometimes add them despite instructions. Do not do any other transformation.
- Validation: parse the JSON to a dict, then validate with LogEvent(**data). 
- Self-repair loop: allow at most 3 total attempts.
    * Attempt 1: send the base prompt.
    * On any failure (network/JSON-decode/Pydantic ValidationError), if attempts remain, build a repair prompt that includes the previous raw model output AND the exact error message, instructing the model to fix it and again return raw JSON only. Retry.
    * After 3 failed attempts, return exactly: {"status": "extraction_failed", "raw": <last raw model output string, or the last exception message if no output was obtained>}
- For this chunk, set confidence to the fixed placeholder string "unvalidated" by overwriting whatever the model returns for confidence BEFORE validation (the real confidence pass is a later task). Always force source_line to equal the line_number argument before validation, regardless of what the model returned.
- On success, return the validated LogEvent instance.

Constraints:
- Only Gemma via Ollama for AI. No other AI APIs.
- Dependencies limited to: standard library, requests, pydantic (via schema import). Add no others.
- No web frameworks, no CLI here, no stdin/stdout handling (that is a later task).
- No files beyond prompts.py and extract.py.
- No placeholder/TODO code (the fixed "unvalidated" confidence is intentional, not a placeholder).
- Never raise out of extract_event for an expected failure — return the failure dict instead. (It is fine to let truly unexpected programmer errors propagate, but network errors, timeouts, JSON errors, and validation errors must be caught and funneled into the retry/failure path.)
- This module prints nothing to stdout or stderr.

Done when: extract_event() returns a valid LogEvent for a parseable suspicious line when Ollama is running, forces source_line to the given line_number, sets confidence to "unvalidated", and returns the failure dict (never crashes) after 3 failed attempts.