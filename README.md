# 🩺 triage

**Turn noisy server logs into clean, structured, validated JSON — using a 100% local Gemma model.**

`triage` reads raw server logs, throws away the noise with a fast deterministic
regex funnel, sends only the *suspicious* lines to a local **Gemma** model (via
[Ollama](https://ollama.com)) to extract structured fields, has the model
**critique its own work** to assign a confidence score, applies a trusted
remediation playbook, and emits strictly-validated JSON.

No cloud. No API keys. Nothing leaves your machine.

---

## ✨ How it works

```
  raw logs (file or stdin)
        │
        ▼
  ┌──────────────┐   pure regex, NO AI
  │  funnel.py   │   keep only suspicious lines (severity keywords)
  └──────────────┘   2000 lines ──► ~80 worth looking at
        │
        ▼
  ┌──────────────┐   🤖 Gemma call #1  → extract structured fields
  │  extract.py  │   🤖 Gemma call #2  → critique + confidence (high/med/low)
  └──────────────┘   + self-repair loop (model fixes its own bad JSON)
        │
        ▼
  ┌──────────────┐   deterministic trusted remediation override, NO AI
  │  playbook.py │
  └──────────────┘
        │
        ▼
  ┌──────────────┐   Pydantic v2 — guarantees valid output
  │  schema.py   │
  └──────────────┘
        │
        ▼
  strictly-validated JSON on stdout   (stats + banner on stderr)
```

**AI is sandwiched between deterministic guardrails:** regex decides *what deserves*
an LLM call (saving tokens), and Pydantic guarantees the output is always valid JSON
no matter what the model says.

---

## 🔧 Prerequisites (run once, before the demo)

```sh
# 1. Make sure the Ollama server is running (leave it in its own terminal tab)
ollama serve

# 2. Pull the model (only needed the first time)
ollama pull gemma2:2b

# 3. Sanity-check both
curl -s http://localhost:11434/api/tags | head -c 80; echo   # server up?
ollama list | grep gemma2                                     # model present?
```

---

## 📦 Install

```sh
cd /Users/manas/gcd_hackathon
pip install -e .
```

This installs a real `triage` command on your PATH (defined in `pyproject.toml`).

> Prefer a clean, isolated install? Use a virtualenv:
> ```sh
> python3 -m venv .venv && source .venv/bin/activate && pip install -e .
> ```

---

## 🚀 Usage — copy-paste blocks

### Show the CLI
```sh
triage --help
```

### Main run — file in, pretty JSON out (fast: 2 events)
```sh
triage sample_logs/hdfs_logs1.txt
```

### Explain *why* lines were flagged (funnel scores → stderr)
```sh
triage sample_logs/hdfs_logs1.txt --explain
```

### Stream mode — JSONL, one event per line
```sh
triage sample_logs/hdfs_logs1.txt --stream
```

### Read from stdin (it's a proper Unix filter)
```sh
cat sample_logs/hdfs_logs1.txt | triage
```

### Live tailing
```sh
tail -f /var/log/app.log | triage --stream
```

### Save the output to a file
```sh
triage sample_logs/hdfs_logs1.txt > events.json            # pretty JSON array
triage sample_logs/hdfs_logs1.txt --stream > events.jsonl  # JSONL
```

### Prove the stdout contract — pipe straight into a JSON parser
```sh
triage sample_logs/hdfs_logs1.txt 2>/dev/null | python3 -m json.tool
```
*(`2>/dev/null` drops the banner + stats; only clean JSON reaches the parser.)*

### Use it as a Python library
```sh
python3 -c "from triage import score_lines, extract_event, LogEvent, __version__; print('triage', __version__, 'API ready')"
```

---

## 🎤 Suggested demo order

| # | Command | What to say |
|---|---------|-------------|
| 1 | `pip install -e .` | "One command installs a real CLI." |
| 2 | `triage --help` | "Banner, file/stdin input, two modes." |
| 3 | `triage sample_logs/hdfs_logs1.txt` | "Logs in → structured JSON out via local Gemma." |
| 4 | `triage sample_logs/hdfs_logs1.txt --explain` | "Full transparency on *why* lines were flagged." |
| 5 | `triage sample_logs/hdfs_logs1.txt --stream` | "JSONL for pipelines / live tailing." |
| 6 | `cat sample_logs/hdfs_logs1.txt \| triage` | "It's a Unix filter." |
| 7 | `triage sample_logs/hdfs_logs1.txt 2>/dev/null \| python3 -m json.tool` | "stdout is ALWAYS valid JSON." |

> ⚠️ For live runs use `sample_logs/hdfs_logs1.txt` (only 2 model calls, ~2s).
> The full `sample_logs/hdfs_logs.txt` is 2000 lines (~80 model calls) — talk about
> it for the *scale* story, don't run it live.

---

## ⚙️ Options

| Flag | Effect |
|------|--------|
| *(none)* | Print one pretty-printed JSON array to stdout. |
| `--stream` | Print JSONL — one compact JSON object per line. |
| `--explain` | Print funnel scores to stderr before extraction (diagnostic). |

---

## 🛟 Output contract

- **Default mode:** one valid JSON array on stdout (possibly empty `[]`).
- **`--stream` mode:** zero or more lines on stdout, each a valid JSON object.
- **Stats, banner, errors → stderr**, never stdout.
- Never crashes with an unhandled traceback; on unexpected errors it still emits
  valid JSON to stdout and exits non-zero.

---

## 🤖 Where is Gemma used?

All AI lives in **`src/triage/extract.py`**, calling local Ollama at
`http://localhost:11434/api/generate` with `model = "gemma2:2b"`:

1. **Extraction** (`extract_event` → `_call_ollama`): reads one raw log line and
   returns structured JSON fields. A self-repair loop (≤3 tries) feeds errors back
   to Gemma to fix its own malformed output.
2. **Confidence critique** (`_confidence_pass`): a second, adversarial call where
   Gemma reviews its own extraction and rates it `high` / `medium` / `low`.

Everything else — the funnel, the playbook, and validation — is fully deterministic.

---

## 🆘 If something breaks live

| Symptom | Fix |
|---------|-----|
| `triage: command not found` | re-run `pip install -e .` (or `source .venv/bin/activate`) |
| every event is `extraction_failed` | Ollama not running → `ollama serve`; model missing → `ollama pull gemma2:2b` |
| seems to hang | check the file path; bare `triage` with no input prints a hint instead |
| want it faster | always demo with `hdfs_logs1.txt`, never the 2000-line file |

---

## 📁 Project layout

```
gcd_hackathon/
├── pyproject.toml          # packaging + `triage` entry point
├── README.md
├── src/triage/
│   ├── __init__.py         # public API + __version__
│   ├── cli.py              # CLI entry point (main)
│   ├── funnel.py           # regex suspicious-line filter (no AI)
│   ├── extract.py          # 🤖 Gemma extraction + confidence critique
│   ├── prompts.py          # SYSTEM_PROMPT + CRITIQUE_PROMPT
│   ├── playbook.py         # deterministic remediation overrides (no AI)
│   └── schema.py           # Pydantic LogEvent model
└── sample_logs/            # demo log files
```
