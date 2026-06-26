import enum

from pydantic import BaseModel


class Severity(str, enum.Enum):
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"


class LogEvent(BaseModel):
    service_name: str
    timestamp: str
    error_severity: Severity
    suggested_remediation: str
    source_line: int
    confidence: str
    schema_version: str = "1.0"
