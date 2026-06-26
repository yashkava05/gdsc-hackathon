# triage — Hackathon Demo Runbook

A fresh-terminal, copy-paste demo. Each step has the command and a one-line talking point.

---

## 0. Before you start (do this OFF-stage, once)

Make sure Ollama is running and the model is present. These are the only external
dependencies — everything else is pure Python.

```sh
# Is the Ollama server up? (should print JSON)
curl -s http://localhost:11434/api/tags | head -c 80; echo

# Is the model pulled? (should list gemma2:2b)
ollama list | grep gemma2
```

If the server is NOT up, start it (leave it running in its own terminal/tab):
```sh
ollama serve
```
If the model is missing:
```sh
ollama pull gemma2:2b
```

---

## 1. Open a FRESH terminal and go to the project

```sh
cd /Users/manas/gcd_hackathon
ls
```
**Say:** "Here's our project — a clean Python `src/` layout package called `triage`."

---

## 2. Install the package (this is the "it's a real package" moment)

```sh
pip install -e .
```
**Say:** "One command installs it from `pyproject.toml`. The `[project.scripts]`
entry point gives us a real `triage` command on the PATH — no `python3 script.py`."

> Already installed on this machine, so this is instant. If you want a truly clean
> "from scratch" look, do it in a throwaway virtualenv instead:
> ```sh
> python3 -m venv .venv && source .venv/bin/activate && pip install -e .
> ```

---

## 3. Prove the command exists and show the UX

```sh
triage --help
```
**Say:** "Notice the usage examples and the banner — it reads from files or stdin,
and has `--stream` and `--explain` modes."

```sh
triage
```
**Say:** "Run it with no input on a bare terminal and it doesn't hang — it prints a
helpful hint and exits. Good CLI hygiene." (It prints the usage hint to stderr.)

---

## 4. THE MAIN DEMO — run it on a real log file (fast: ~2 events)

```sh
triage sample_logs/hdfs_logs1.txt
```
**Say:** "207 raw HDFS log lines go in. A deterministic regex funnel throws away the
noise and keeps only the suspicious lines. Each survivor goes to a local Gemma model
via Ollama, which extracts structured fields. The output is strictly-validated JSON
on stdout; the stats you see are on stderr."

---

## 5. Show `--explain` (why these lines?)

```sh
triage sample_logs/hdfs_logs1.txt --explain
```
**Say:** "`--explain` shows the funnel's scoring on stderr — full transparency on
*why* a line was flagged — while stdout stays clean JSON."

---

## 6. Show `--stream` (JSONL, one object per line)

```sh
triage sample_logs/hdfs_logs1.txt --stream
```
**Say:** "Stream mode emits JSONL — one event per line — ideal for piping into other
tools or tailing a live log."

---

## 7. Show the Unix-pipe story (stdin)

```sh
cat sample_logs/hdfs_logs1.txt | triage --stream
```
**Say:** "It's a proper Unix filter. Same result piping from stdin — so
`tail -f app.log | triage --stream` gives you live triage."

---

## 8. The stdout contract (the engineering flex)

```sh
triage sample_logs/hdfs_logs1.txt 2>/dev/null | python3 -m json.tool
```
**Say:** "stdout is ALWAYS valid JSON — diagnostics, stats, banner all go to stderr.
Here we throw stderr away and pipe stdout straight into a JSON parser. It just works."

---

## 9. It's also a library (importable package)

```sh
python3 -c "from triage import score_lines, extract_event, LogEvent, __version__; print('triage', __version__, '- API ready')"
```
**Say:** "Beyond the CLI, it's an importable package — `score_lines`, `extract_event`,
and the `LogEvent` Pydantic model are all part of the public API."

---

## 10. (Optional) Scale story

```sh
wc -l sample_logs/hdfs_logs.txt          # 2000 lines
```
**Say:** "On the full 2000-line file the funnel narrows it to 80 lines before we ever
touch the model — so we only spend LLM calls on what matters. (We don't run this live;
it's ~80 model calls.)"

---

## If something goes wrong live

- **`triage: command not found`** → re-run `pip install -e .` (or `source .venv/bin/activate`).
- **Every event is `extraction_failed`** → Ollama isn't running or model missing:
  `ollama serve` (in another tab) and `ollama pull gemma2:2b`.
- **It seems to hang** → you piped nothing / wrong path. Ctrl-C, check the file path.
- **Want it faster** → use `hdfs_logs1.txt` (2 events), never the big file, for live runs.
