I have a working command-line tool made of these files in the current directory: schema.py, funnel.py, prompts.py, extract.py, playbook.py, triage.py, plus a sample_logs/ directory and a requirements.txt. The tool reads server logs from stdin, filters them, sends suspicious lines to a local Gemma model via Ollama, and prints validated JSON to stdout with stats to stderr.

This task converts the project into an installable Python package and adds file-path input. Do BOTH parts. Do not change any of the core logic (funnel scoring, Ollama calls, validation/repair loop, confidence pass, playbook) — only restructure files, fix imports, add the file-path argument, and add packaging config.

=== PART 1: Restructure into a package ===

Create this exact layout using a src layout:

  pyproject.toml          (new, at project root)
  README.md               (new, at project root)
  src/triage/__init__.py  (new)
  src/triage/schema.py    (moved from ./schema.py, unchanged except imports)
  src/triage/funnel.py    (moved from ./funnel.py, unchanged)
  src/triage/prompts.py   (moved from ./prompts.py, unchanged)
  src/triage/extract.py   (moved from ./extract.py, imports fixed)
  src/triage/playbook.py  (moved from ./playbook.py, imports fixed)
  src/triage/cli.py       (moved from ./triage.py, imports fixed + file-arg added — see Part 2)

Keep sample_logs/ where it is at the project root. Delete the old top-level .py files after moving them into src/triage/ (do not leave duplicates). Do not delete sample_logs/ or requirements.txt.

Fix all cross-module imports to be relative within the package. Every import of one project module from another must become a relative import, e.g.:
  `from schema import LogEvent, Severity`  ->  `from .schema import LogEvent, Severity`
  `from funnel import score_lines`         ->  `from .funnel import score_lines`
  `from prompts import SYSTEM_PROMPT`      ->  `from .prompts import SYSTEM_PROMPT`
  `from prompts import CRITIQUE_PROMPT`    ->  `from .prompts import CRITIQUE_PROMPT`
  `from extract import extract_event`      ->  `from .extract import extract_event`
  `from playbook import apply_playbook`    ->  `from .playbook import apply_playbook`
Do NOT change imports of standard-library or third-party modules (json, sys, argparse, re, requests, pydantic) — those stay absolute.

src/triage/__init__.py contents:
  - Define `__version__ = "0.1.0"`
  - Re-export the main public API so `from triage import ...` works:
      from .schema import LogEvent, Severity
      from .funnel import score_lines
      from .extract import extract_event
      from .playbook import apply_playbook

pyproject.toml contents (use the hatchling build backend):
  [project]
  name = "triage"
  version = "0.1.0"
  description = "Filter noisy server logs with regex, extract structured events with a local Gemma model via Ollama, and emit strictly-validated JSON."
  requires-python = ">=3.10"
  dependencies = ["pydantic>=2", "requests"]

  [project.scripts]
  triage = "triage.cli:main"

  [build-system]
  requires = ["hatchling"]
  build-backend = "hatchling.build"

  [tool.hatch.build.targets.wheel]
  packages = ["src/triage"]

=== PART 2: Add file-path input to the CLI (in src/triage/cli.py) ===

Keep ALL existing behavior (--stream, --explain, the stdout-is-always-valid-JSON contract, stats to stderr, the main() entry point and the `if __name__ == "__main__": main()` guard). Add these changes using argparse:

1. Add an optional positional argument:
     paths: zero or more log file paths (nargs="*").
2. Input-source logic:
   - If one or more paths are given: read and concatenate the lines of those files in the given order. Use these as the input lines instead of stdin.
   - If NO paths are given: read from stdin exactly as the tool does now.
   - If a given path does not exist or cannot be read: print a clear error to STDERR (e.g. "triage: cannot read <path>: <reason>"), skip that file, and continue with any remaining files. Do not crash, do not print errors to stdout.
3. No-input guard:
   - If no paths are given AND stdin is empty/not connected to a pipe (sys.stdin.isatty() is True), do NOT hang waiting for input. Instead print a short usage hint to STDERR, e.g.:
       "triage: no input. Provide a log file (triage app.log) or pipe logs in (cat app.log | triage). See --help."
     then exit with a nonzero status. (When stdin IS piped, read it as normal even with no paths.)
4. argparse help text:
   - Set a program description and add usage examples in the epilog so `triage --help` shows:
       triage app.log
       triage logs/*.log
       cat app.log | triage
       tail -f app.log | triage --stream
   - Document --stream and --explain with one-line help strings.

The stdout contract is unchanged: default mode prints one JSON array; --stream prints one JSON object per line; all diagnostics/stats/errors go to stderr; never crash with an unhandled traceback.

=== Constraints ===
- Only Gemma via Ollama for AI; no other AI APIs.
- Dependencies stay exactly: pydantic>=2, requests (plus standard library). Add no others. hatchling is a build requirement, not a runtime dependency — it goes only in [build-system].
- Do not alter funnel scoring, the Ollama call details, the validation/repair loop, the confidence pass, or the playbook logic.
- No placeholder/TODO code.
- After this task, the old top-level .py files must be gone (moved into src/triage/), and `pip install -e .` must make a working `triage` command.

Done when: `pip install -e .` succeeds, `triage sample_logs/hdfs_logs.txt --stream` produces the same JSONL output the old `python3 triage.py --stream < sample_logs/hdfs_logs.txt` did, `cat sample_logs/hdfs_logs.txt | triage` also works, `triage --help` shows the usage examples, and bare `triage` in a terminal with no pipe prints the usage hint instead of hanging.

Add a module-level ASCII-art banner string for "TRIAGE" and a private _show_banner() function that prints it to stderr only when sys.stderr.isatty() is True; call it once at the start of main() before reading input. The banner must never go to stdout and must not appear when output is piped or redirected. It must not interfere with the stdout JSON contract or the --stream/--explain/file-path behavior.