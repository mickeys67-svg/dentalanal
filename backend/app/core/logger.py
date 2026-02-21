import logging
import sys
import os
from logging.handlers import RotatingFileHandler

def setup_logging(log_level=logging.INFO):
    """
    Sets up centralized logging for the application.
    Logs to both console (stdout) and file (logs/server.log).

    In Cloud Run, uses /tmp for writable location.
    """
    # Determine logs directory (use /tmp in Cloud Run, ./logs locally)
    if os.environ.get('K_SERVICE'):  # Running in Cloud Run
        log_dir = "/tmp/logs"
    else:
        # Get the absolute path to backend directory
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_dir = os.path.join(backend_dir, "logs")

    # Create logs directory if it doesn't exist
    try:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
    except (PermissionError, OSError) as e:
        # If we can't create logs directory, fail gracefully
        print(f"[WARNING] Cannot create logs directory: {e}")
        # Continue with console-only logging
        log_file = None

        # Set up console-only logging
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        if root_logger.handlers:
            root_logger.handlers.clear()

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # Suppress noisy libraries
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("apscheduler").setLevel(logging.INFO)

        logging.warning(f"Logging to console only (no file)")
        return

    log_file = os.path.join(log_dir, "server.log")

    # Formatters
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    if root_logger.handlers:
        root_logger.handlers.clear()

    # 1. Console Handler with UTF-8 encoding
    # Force UTF-8 encoding for console output (important for Cloud Run)
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass  # Ignore if stdout doesn't support reconfigure

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 2. File Handler (Rotating)
    # Max 10MB per file, keep last 5 files
    try:
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10485760, backupCount=5, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        logging.info(f"Logging configured. Writing to {log_file}")
    except (PermissionError, OSError) as e:
        logging.warning(f"Cannot create log file at {log_file}: {e}")
        logging.warning("Logging to console only")

    # Suppress noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.INFO)
