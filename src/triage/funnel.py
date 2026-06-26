import re

_TIER_KEYWORDS = [
    (4, ("FATAL",)),
    (3, ("ERROR",)),
    (2, ("WARN", "WARNING")),
    (1, ("INFO",)),
]

_SUSPICIOUS_KEYWORDS = (
    "exception",
    "fail",
    "failed",
    "failure",
    "panic",
    "fatal",
    "critical",
    "traceback",
)

_TIER_PATTERNS = [
    (score, re.compile(r"\b(?:%s)\b" % "|".join(words), re.IGNORECASE))
    for score, words in _TIER_KEYWORDS
]

_SUSPICIOUS_PATTERN = re.compile(
    r"\b(?:%s)\b" % "|".join(_SUSPICIOUS_KEYWORDS), re.IGNORECASE
)


def score_lines(lines: list[str]) -> list[tuple[int, str, int]]:
    results = []
    for index, raw in enumerate(lines):
        text = raw.rstrip("\r\n").rstrip()
        score = 0
        for tier_score, pattern in _TIER_PATTERNS:
            if pattern.search(text):
                score = tier_score
                break
        if _SUSPICIOUS_PATTERN.search(text):
            score = max(score, 3)
        if score >= 2:
            results.append((index + 1, text, score))
    results.sort(key=lambda item: item[2], reverse=True)
    return results
