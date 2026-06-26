# triage

Filter noisy server logs with regex, extract structured events with a local
[Gemma](https://ai.google.dev/gemma) model via [Ollama](https://ollama.com),
and emit strictly-validated JSON.

`triage` reads raw server logs, keeps only the suspicious lines (a deterministic,
format-agnostic regex funnel based on universal severity keywords), sends each
survivor to a local Gemma model for structured extraction, adversarially
critiques the extraction to assign a confidence, applies a trusted remediation
playbook, and prints validated JSON. The stdout stream is **always** valid JSON;
all diagnostics and statistics go to stderr.

## Requirements

- Python >= 3.10
- [Ollama](https://ollama.com) running locally with the `gemma2:2b` model:
  ```sh
  ollama pull gemma2:2b
  ```

## Install

```sh
pip install -e .
```

This installs a `triage` command.

## Usage

```sh
triage app.log                  # read one or more log files
triage logs/*.log               # multiple files, concatenated in order
cat app.log | triage            # read from stdin
tail -f app.log | triage --stream   # stream JSONL as lines arrive
```

### Options

- `--stream` — emit JSONL (one compact JSON object per line) instead of a single
  JSON array.
- `--explain` — print the funnel scores to stderr before extraction (diagnostic).

Run `triage --help` for the full usage reference.

## Output contract

- **Default mode:** one valid JSON array on stdout (possibly empty `[]`).
- **`--stream` mode:** zero or more lines on stdout, each a valid JSON object.
- Statistics (lines read, suspicious, succeeded, failed) and all errors go to
  **stderr**, never stdout.
- The program never crashes with an unhandled traceback; on unexpected errors it
  still emits valid JSON to stdout and exits non-zero.

## Package API

```python
from triage import LogEvent, Severity, score_lines, extract_event, apply_playbook
```
