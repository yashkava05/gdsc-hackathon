import json

import requests

from schema import LogEvent, Severity
from prompts import SYSTEM_PROMPT

_OLLAMA_URL = "http://localhost:11434/api/generate"
_MODEL = "gemma2:2b"
_TIMEOUT = 30
_MAX_ATTEMPTS = 3


class OllamaNetworkError(RuntimeError):
    """Raised when the Ollama HTTP request itself fails (connection, timeout, etc.)."""


class OllamaResponseError(RuntimeError):
    """Raised when Ollama responds but the body is unusable (bad status, missing key, error field)."""


def _call_ollama(prompt: str) -> str:
    body = {
        "model": _MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.1, "num_predict": 256},
    }
    try:
        response = requests.post(_OLLAMA_URL, json=body, timeout=_TIMEOUT)
    except requests.exceptions.RequestException as exc:
        raise OllamaNetworkError(f"Network error contacting Ollama: {exc}") from exc

    if response.status_code != 200:
        raise OllamaResponseError(
            f"Ollama returned HTTP {response.status_code}: {response.text[:200]}"
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise OllamaResponseError(f"Ollama response is not valid JSON: {exc}") from exc

    if "error" in payload:
        raise OllamaResponseError(f"Ollama error: {payload['error']}")

    if "response" not in payload:
        raise OllamaResponseError(
            f"Ollama response missing 'response' key. Keys present: {list(payload.keys())}"
        )

    return payload["response"]


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text[3:]
        newline = text.find("\n")
        if newline != -1 and text[:newline].strip().lower() in ("", "json"):
            text = text[newline + 1:]
        if text.endswith("```"):
            text = text[:-3]
    return text.strip()


def _base_prompt(line_number: int, line: str) -> str:
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"The source_line value MUST be exactly the integer {line_number}.\n\n"
        f"Analyze this single log line and return the JSON object:\n{line}"
    )


def _repair_prompt(line_number: int, line: str, previous_output: str, error_message: str) -> str:
    return (
        f"{_base_prompt(line_number, line)}\n\n"
        f"Your previous response was invalid and must be fixed.\n"
        f"Previous response:\n{previous_output}\n\n"
        f"Error:\n{error_message}\n\n"
        f"Fix the problem and return raw JSON only, with no markdown fences, "
        f"backticks, or prose. Remember source_line must equal {line_number}."
    )


def extract_event(line_number: int, line: str) -> LogEvent | dict:
    last_raw = None
    last_error = None
    prompt = _base_prompt(line_number, line)

    for attempt in range(_MAX_ATTEMPTS):
        if attempt > 0:
            previous_output = last_raw if last_raw is not None else (last_error or "")
            prompt = _repair_prompt(line_number, line, previous_output, last_error or "")
        try:
            raw = _call_ollama(prompt)
            last_raw = raw
            data = json.loads(_strip_code_fence(raw))
            data["confidence"] = "unvalidated"
            data["source_line"] = line_number
            return LogEvent(**data)
        except OllamaNetworkError as exc:
            last_error = str(exc)
            break  # network is down — retrying will not help
        except Exception as exc:
            last_error = str(exc)

    raw_for_failure = last_raw if last_raw is not None else (last_error or "")
    return {"status": "extraction_failed", "raw": raw_for_failure}
