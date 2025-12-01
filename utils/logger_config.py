import logging
from datetime import datetime
from pathlib import Path
from typing import Optional


def sanitize_log_name(log_name: str) -> str:
    """Convert log names into safe filesystem-friendly names."""
    sanitized = log_name.strip().strip("/\\")
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', ' ']
    for char in invalid_chars:
        sanitized = sanitized.replace(char, "_")
    return sanitized or "default_logger"

def setup_logging(log_name: Optional[str] = None) -> logging.Logger:
    """
    Create a logger that outputs to both console and a file.
    Log files are stored under ~/.local/aquatic/logs with optional nested structure.

    Args:
        log_name: The name or nested path for the log group, e.g. "pipeline" or "pipeline/news".
    """
    log_name = log_name or "default_logger"
    logger = logging.getLogger(log_name)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Base log directory in ~/.local/aquatic/logs
    base_dir = Path.home() / ".local" / "aquatic" / "logs"
    base_dir.mkdir(parents=True, exist_ok=True)

    # Handle nested log names
    parts = [p for p in Path(log_name).parts if p.strip()]
    sanitized_parts = [sanitize_log_name(part) for part in parts]

    if len(sanitized_parts) > 1:
        nested_dir = base_dir.joinpath(*sanitized_parts[:-1])
    else:
        nested_dir = base_dir

    nested_dir.mkdir(parents=True, exist_ok=True)

    # Final log file path
    log_file = nested_dir / f"{sanitized_parts[-1]}_{datetime.now():%Y-%m-%d}.log"

    # Handlers
    file_handler = logging.FileHandler(log_file)
    console_handler = logging.StreamHandler()

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger.setLevel(logging.INFO)

    # Base log directory in ~/.local/aquatic/logs
    base_dir = Path.home() / ".local" / "aquatic" / "logs"
    base_dir.mkdir(parents=True, exist_ok=True)

    # Handle nested log names
    parts = [p for p in Path(log_name).parts if p.strip()]
    sanitized_parts = [sanitize_log_name(part) for part in parts]
    
    if len(sanitized_parts) > 1:
        nested_dir = base_dir.joinpath(*sanitized_parts[:-1])
    else:
        nested_dir = base_dir

    nested_dir.mkdir(parents=True, exist_ok=True)
    
    # Final log file path
    log_file = nested_dir / f"{sanitized_parts[-1]}_{datetime.now():%Y-%m-%d}.log"
    
    # Handlers
    file_handler = logging.FileHandler(log_file)
    console_handler = logging.StreamHandler()
    
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

