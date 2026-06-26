import sys
import json
import argparse
import traceback

from .funnel import score_lines
from .extract import extract_event
from .schema import LogEvent

_BANNER = r"""
 _____ ____  ___    _    ____ _____
|_   _|  _ \|_ _|  / \  / ___| ____|
  | | | |_) || |  / _ \| |  _|  _|
  | | |  _ < | | / ___ \ |_| | |___
  |_| |_| \_\___/_/   \_\____|_____|

  log triage  -  regex funnel + local Gemma extraction
"""


def _show_banner():
    if sys.stderr.isatty():
        print(_BANNER, file=sys.stderr)


def _read_lines(paths):
    if paths:
        lines = []
        for path in paths:
            try:
                with open(path, "r") as handle:
                    lines.extend(handle.read().splitlines())
            except OSError as exc:
                print(f"triage: cannot read {path}: {exc}", file=sys.stderr)
                continue
        return lines
    return sys.stdin.read().splitlines()


def main():
    _show_banner()

    parser = argparse.ArgumentParser(
        prog="triage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Filter noisy server logs with a regex funnel, extract structured "
            "events with a local Gemma model via Ollama, and emit strictly-"
            "validated JSON to stdout (stats and diagnostics go to stderr)."
        ),
        epilog=(
            "examples:\n"
            "  triage app.log\n"
            "  triage logs/*.log\n"
            "  cat app.log | triage\n"
            "  tail -f app.log | triage --stream\n"
        ),
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="zero or more log file paths; if omitted, logs are read from stdin.",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="emit JSONL (one compact JSON object per line) instead of a JSON array.",
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="print funnel scores to stderr before extraction (diagnostic only).",
    )
    args = parser.parse_args()
    stream = args.stream

    if not args.paths and sys.stdin.isatty():
        print(
            "triage: no input. Provide a log file (triage app.log) or pipe logs "
            "in (cat app.log | triage). See --help.",
            file=sys.stderr,
        )
        sys.exit(2)

    total = 0
    suspicious = []
    results = []
    success = 0
    failed = 0
    stdout_done = False
    exit_code = 0

    try:
        lines = _read_lines(args.paths)
        total = len(lines)

        suspicious = score_lines(lines)

        if args.explain:
            for line_number, line_text, score in suspicious:
                print(
                    f"score={score} line={line_number}: {line_text}",
                    file=sys.stderr,
                )

        for line_number, line_text, score in suspicious:
            result = extract_event(line_number, line_text)
            if isinstance(result, LogEvent):
                entry = result.model_dump()
                success += 1
            else:
                entry = result
                failed += 1

            if stream:
                print(json.dumps(entry, separators=(",", ":")))
            else:
                results.append(entry)

        if not stream:
            sys.stdout.write(json.dumps(results) + "\n")
            stdout_done = True

    except Exception:
        exit_code = 1
        if not stream and not stdout_done:
            sys.stdout.write(json.dumps(results) + "\n")
            stdout_done = True
        print("triage: unexpected error during processing:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)

    finally:
        print(f"total lines read: {total}", file=sys.stderr)
        print(f"suspicious lines (sent to extraction): {len(suspicious)}", file=sys.stderr)
        print(f"successful extractions: {success}", file=sys.stderr)
        print(f"failed extractions: {failed}", file=sys.stderr)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
