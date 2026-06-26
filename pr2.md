We are building a command-line Python utility called `triage`. A file `schema.py` already exists (defines LogEvent and Severity) — do not modify it. This task ONLY creates the deterministic regex filter. Do not build any other part of the project.

Create exactly one file: `funnel.py`
Do not create, modify, or stub any other files.

funnel.py — pure standard library (use the `re` module). No AI, no network calls, no Pydantic needed here.

Define exactly one public function with this exact signature:

    def score_lines(lines: list[str]) -> list[tuple[int, str, int]]:

Behavior:
- Input is a list of raw log line strings (already split, no trailing newlines guaranteed — strip trailing newlines defensively).
- For each line, compute an integer suspicion score by matching UNIVERSAL severity keywords, case-insensitively, as whole words using regex word boundaries. Use exactly this keyword-to-score mapping:
      FATAL  -> 4
      ERROR  -> 3
      WARN   -> 2   (also match the whole word "WARNING")
      INFO   -> 1
  A line's score is the score of the HIGHEST-severity keyword it contains (not a sum). For example a line containing both "WARN" and "ERROR" scores 3.
- Additionally, these keywords each add nothing extra to the tier but DO make an otherwise-unmatched line suspicious at score 3 (ERROR tier), matched case-insensitively as whole words: "exception", "fail", "failed", "failure", "panic", "fatal", "critical", "traceback".
  (Note "fatal" here is redundant with the FATAL tier; if a line matches both FATAL and one of these, it stays at the highest tier.)
- A line is "suspicious" and included in the output ONLY if its score is >= 2 (i.e. WARN tier or above). INFO-only lines (score 1) and lines matching no keywords (score 0) are excluded.
- line_number is 1-based, corresponding to the line's position in the input list (the first line is 1).
- Return a list of (line_number, line_text, score) tuples for suspicious lines only, sorted by score DESCENDING. For equal scores, preserve original input order (stable sort).
- line_text in the output is the original line with trailing newline/whitespace stripped.

CRITICAL format-agnostic requirement:
- The filter MUST be format-agnostic. Use ONLY universal severity keywords as above. Do NOT detect log formats, do NOT branch on format, do NOT special-case any particular log layout (no HDFS-specific or Linux-specific logic). The identical code will be validated against both samples/hdfs_logs.txt and samples/linux_logs.txt and must work on both with no changes.

Constraints:
- Standard library only (the `re` module). No third-party dependencies, no requests, no pydantic.
- No web frameworks, no AI APIs, no network calls.
- No files beyond funnel.py.
- No placeholder code, no TODO comments.
- No printing to stdout or stderr — this module only returns data.

Done when: score_lines() returns suspicious lines sorted by score descending, with correct 1-based line numbers, and the exact same code produces sensible results on both sample files.