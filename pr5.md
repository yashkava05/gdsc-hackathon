We are building a command-line Python utility called `triage`. These files already exist: schema.py (LogEvent, Severity), funnel.py (score_lines), prompts.py (SYSTEM_PROMPT), extract.py (extract_event, with private helpers _call_ollama, _base_prompt, _repair_prompt, _strip_code_fence, _strip_code_fence and constants _OLLAMA_URL, _MODEL, _TIMEOUT, _MAX_ATTEMPTS), triage.py (main entry point). 

This task does TWO things: (1) add an adversarial confidence pass inside extract.py, and (2) create a new file playbook.py and wire it into the extraction flow. The ONLY AI model allowed is Gemma via Ollama (http://localhost:11434/api/generate, model gemma2:2b). No other AI APIs.

Create exactly one new file: `playbook.py`
Edit exactly these existing files: `extract.py`, and `prompts.py` (only to add one new prompt constant). 
Do NOT modify schema.py, funnel.py, triage.py, or any other file.

--- prompts.py (edit: ADD one constant, do not change SYSTEM_PROMPT) ---
Add exactly one new string constant:
    CRITIQUE_PROMPT: str
It instructs the model to act as an adversarial reviewer of a log-extraction it is given. It must:
  - Receive the original log line and the extracted JSON.
  - Critically assess whether the extraction is accurate and well-supported by the line.
  - Output raw JSON ONLY (no markdown, no prose) containing exactly one key: "confidence", whose value is one of exactly these three strings: "high", "medium", "low".
  - "high" only if the extraction is fully supported by the line; "low" if it is largely guessed or unsupported; "medium" otherwise.

--- extract.py (edit) ---
Keep the existing extract_event signature and all existing behavior, with these changes:
1. Remove the hardcoded confidence = "unvalidated" override. Instead, after a LogEvent is successfully validated, run an adversarial confidence pass:
   - Add a private function `def _confidence_pass(line: str, event: LogEvent) -> str:` that builds a prompt from CRITIQUE_PROMPT (import it from prompts) plus the original line and the event's JSON (event.model_dump_json()), calls _call_ollama, strips fences with the existing helper, json.loads it, and reads the "confidence" value.
   - It must return one of "high"/"medium"/"low". If the critique call fails for ANY reason (network, JSON error, missing/invalid key, value not in the allowed set), return "low" as a safe default. Never raise out of _confidence_pass.
   - Set event.confidence to the returned value (re-validate or use model_copy/direct assignment consistent with Pydantic v2; the field is a str so direct assignment is fine).
2. After the confidence pass, apply the playbook: import apply_playbook from playbook and call event = apply_playbook(event) before returning. 
3. The failure dict path is unchanged: a terminal extraction failure still returns {"status": "extraction_failed", "raw": ...} and never reaches the confidence/playbook steps.
4. source_line is still forced to the line_number argument as before.

--- playbook.py (new) ---
Imports allowed: standard library, and from schema import LogEvent. No third-party imports, no AI, no network calls — this file is fully deterministic.
Define exactly:
  - REMEDIATIONS: dict[str, str]  — a mapping from lowercase error keyword to a trusted remediation string. Include at least these sensible entries (you may add a few more obviously-useful ones, but keep them generic and format-agnostic):
        "out of memory": "Increase heap/memory allocation or investigate a memory leak; restart the affected service."
        "connection refused": "Verify the target service is running and listening on the expected port; check firewall and network routes."
        "timeout": "Increase the timeout threshold if appropriate and investigate downstream latency or resource contention."
        "disk full": "Free disk space or expand the volume; rotate and archive old logs."
        "permission denied": "Check file/resource ownership and permissions; verify the running user has required access."
        "null pointer": "Add a null/None check at the failing call site and validate upstream inputs."
        "authentication failure": "Verify credentials and auth configuration; check for expired tokens or keys."
  - def apply_playbook(event: LogEvent) -> LogEvent:
        Behavior: case-insensitively search the event's suggested_remediation AND service_name AND timestamp? NO — only search a relevant text field. Specifically: search the lowercase of the event's suggested_remediation and source-derived text is not available here, so search the lowercase of suggested_remediation for any REMEDIATIONS key. 
        CLARIFICATION: match against the lowercased concatenation of event.suggested_remediation. If any REMEDIATIONS key appears as a substring, OVERRIDE event.suggested_remediation with the corresponding trusted value. If multiple keys match, use the first match by iteration order of REMEDIATIONS. If no key matches, return the event unchanged.
        Return the (possibly modified) LogEvent. Direct attribute assignment is fine (suggested_remediation is a str).
        Never raise; if anything unexpected occurs, return the event unchanged.

Constraints:
- Only Gemma via Ollama for AI; playbook.py has NO AI and NO network.
- Dependencies limited to standard library, requests, pydantic (via schema). No new deps.
- New file: only playbook.py. Edits: only extract.py and prompts.py. Do not touch triage.py, funnel.py, schema.py.
- No web frameworks, no placeholder/TODO code.
- extract.py still prints nothing to stdout/stderr and still never crashes on expected failures.
- The stdout contract from triage.py must remain intact (these changes only affect the LogEvent contents, not output formatting).

Done when: extract_event returns a LogEvent whose confidence is "high"/"medium"/"low" (from the adversarial pass, "low" on any critique failure), with suggested_remediation overridden by the playbook when a known keyword matches, and the failure dict path unchanged.