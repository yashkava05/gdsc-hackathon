We are building a command-line Python utility called `triage`. These files already exist and must NOT be modified: schema.py (LogEvent, Severity), funnel.py (score_lines), prompts.py (SYSTEM_PROMPT), extract.py (extract_event). This task creates the command-line entry point only. Do not build any other part of the project.

Create exactly one file: `triage.py`
Do not create, modify, or stub any other files.

triage.py imports allowed: standard library (sys, json, argparse), and from the existing modules: from funnel import score_lines, from extract import extract_event, from schema import LogEvent. No third-party imports, no other AI APIs.

Behavior — the program is a stdin→stdout filter:
- Read ALL of stdin as text, split into lines.
- Pass the lines to score_lines() to get suspicious (line_number, line_text, score) tuples, already sorted by score descending.
- For each suspicious tuple, call extract_event(line_number, line_text). Its return is either a LogEvent or a failure dict {"status": "extraction_failed", ...}.
- Convert each result to a plain JSON-serializable dict:
    * If it is a LogEvent, use its model_dump() (Pydantic v2).
    * If it is already a dict (failure dict), use it as-is.
- Default output mode (no flags): print to STDOUT a single JSON array containing all result dicts in order, using json.dumps. This must be ONE valid JSON document.

Command-line flags (use argparse):
  --stream : instead of a JSON array, print JSONL to stdout — one compact JSON object per line, one line per result, in the same order. (No surrounding array brackets.)
  --explain : print the funnel scores to STDERR before extraction — for each suspicious line, a human-readable line like "score=<score> line=<line_number>: <line_text>". This is diagnostic only and must go to stderr, never stdout.
  The two flags are independent and may be combined.

Statistics to STDERR (always, regardless of flags), printed AFTER processing:
  - total lines read
  - number of suspicious lines (sent to extraction)
  - number of successful extractions (LogEvent results)
  - number of failed extractions (failure dicts)
  Format them as readable text lines, clearly labeled. All of this goes to stderr.

THE STDOUT CONTRACT (critical):
- stdout must ALWAYS be valid JSON: in default mode a single valid JSON array (possibly empty: []), in --stream mode zero or more lines each of which is a valid JSON object.
- Never print diagnostics, logs, stats, or prose to stdout. Only the JSON result(s).
- The program must NEVER crash with an unhandled exception. Wrap the main logic so that if anything unexpected happens, it still prints valid JSON to stdout (in default mode, at minimum an empty array []; in stream mode, nothing or only the valid lines produced so far) and writes the error to stderr, then exits with a nonzero status code. A clean run exits 0.
- If stdin is empty, suspicious count is 0: print [] (default) or nothing (stream) to stdout, still print stats to stderr, exit 0.

Provide a standard `if __name__ == "__main__":` guard calling a main() function.

Constraints:
- Standard library + existing project modules only. No new third-party deps, no web frameworks, no other AI APIs.
- No files beyond triage.py.
- No placeholder/TODO code.
- stdout stays clean JSON in every mode and every error path.
- Do not modify any existing file.

Done when: `cat samples/hdfs_logs.txt | python3 triage.py` prints a valid JSON array to stdout and stats to stderr; --stream prints valid JSONL; --explain prints scores to stderr; empty stdin prints [] and exits 0; and stdout is parseable JSON in all cases.