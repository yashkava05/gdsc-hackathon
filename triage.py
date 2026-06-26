import sys
import json
import argparse
import traceback

from funnel import score_lines
from extract import extract_event
from schema import LogEvent


def main():
    parser = argparse.ArgumentParser(
        description="triage: filter log lines on stdin and emit structured JSON on stdout."
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

    total = 0
    suspicious = []
    results = []
    success = 0
    failed = 0
    stdout_done = False
    exit_code = 0

    try:
        data = sys.stdin.read()
        lines = data.splitlines()
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
