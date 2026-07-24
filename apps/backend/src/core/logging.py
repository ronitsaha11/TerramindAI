import logging
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the LogRecord.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_record: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Include standard request attributes if they exist
        for attr in ["request_id", "path", "method", "status_code", "duration"]:
            if hasattr(record, attr):
                log_record[attr] = getattr(record, attr)

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)

def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure the root logger with the JSONFormatter.
    """
    logger = logging.getLogger()
    logger.setLevel(log_level.upper())
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)

    # Uvicorn logger overrides
    logging.getLogger("uvicorn.access").handlers = [console_handler]
    logging.getLogger("uvicorn.error").handlers = [console_handler]
