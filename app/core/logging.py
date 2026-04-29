import logging
import sys
from enum import StrEnum
from typing import Optional
from datetime import datetime
from logging.handlers import RotatingFileHandler

try:
    from colorlog import ColoredFormatter

    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    def __str__(self):
        """
        Return the string value of the LogLevel enum member.

        :return: The string value of the LogLevel enum member.
        :rtype: str
        """
        return self.value


class FastAPILogger:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        Ensure that only one instance of the FastAPILogger is created.

        This implementation uses the Singleton pattern to ensure that only a single instance of the FastAPILogger is created.

        :return: The singleton instance of the FastAPILogger.
        :rtype: FastAPILogger
        """
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        level: LogLevel = LogLevel.INFO,
        log_file: Optional[str] = None,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        json_format: bool = False,
        colorize: bool = True,
    ):
        """
        Initialize the logger with enhanced configuration.

        Args:
            level: Minimum logging level (default: INFO)
            log_file: Path to log file (optional)
            max_bytes: Maximum log file size before rotation (default: 10MB)
            backup_count: Number of backup logs to keep (default: 5)
            json_format: Whether to use JSON formatting (default: False)
            colorize: Whether to colorize console output (default: True)
        """
        self._level = level
        self._log_file = log_file
        self._max_bytes = max_bytes
        self._backup_count = backup_count
        self._json_format = json_format
        self._colorize = colorize and COLORLOG_AVAILABLE and not json_format
        self._logger = None

        self._configure_logger()

    @property
    def logger(self) -> logging.Logger:
        """Get the configured logger instance."""
        return self._logger

    def _configure_logger(self) -> None:
        """
        Configure the logger with the provided settings.

        This method sets up the logger with the specified log level, log file, and
        formatting options. It also configures Uvicorn access logs to use the same
        logger configuration.

        :return: None
        :rtype: None
        """
        self._logger = logging.getLogger("fastapi")
        self._logger.setLevel(self._level)

        # Clear existing handlers to avoid duplication
        self._logger.handlers.clear()

        # Create formatters
        if self._json_format:
            formatter = self._create_json_formatter()
        else:
            formatter = self._create_text_formatter(colorized=self._colorize)

        # Console handler (always enabled)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self._level)
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)

        # File handler (if log file specified)
        if self._log_file:
            file_handler = RotatingFileHandler(
                filename=self._log_file,
                maxBytes=self._max_bytes,
                backupCount=self._backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(self._level)
            # File logs should never be colored
            file_handler.setFormatter(self._create_text_formatter(colorized=False))
            self._logger.addHandler(file_handler)

        # Configure Uvicorn access logs to use our logger
        logging.getLogger("uvicorn.access").handlers = [console_handler]
        if self._log_file:
            logging.getLogger("uvicorn.access").addHandler(file_handler)

    def _create_text_formatter(self, colorized: bool = False) -> logging.Formatter:
        """
        Create a text-based log formatter.

        If colorized is True, the formatter will use colorlog to add color to the log messages.
        If colorized is False, the formatter will use the standard logging.Formatter.

        The format string is as follows:
        - %(asctime)s: The timestamp of the log message.
        - %(levelname)s: The log level name.
        - %(name)s: The name of the logger.
        - %(filename)s:%(lineno)d: The filename and line number of the log message.
        - %(message)s: The log message itself.

        :param colorized: Whether to use colorlog to add color to the log messages.
        :type colorized: bool
        :return: A text-based log formatter.
        :rtype: logging.Formatter
        """
        if self._level == LogLevel.DEBUG:
            fmt = "%(asctime)s [%(levelname)s] [%(name)s:%(filename)s:%(lineno)d] %(message)s"
        else:
            fmt = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"

        if colorized:
            return ColoredFormatter(
                "%(log_color)s" + fmt,
                datefmt="%Y-%m-%d %H:%M:%S",
                reset=True,
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold_purple",
                },
                secondary_log_colors={},
                style="%",
            )
        return logging.Formatter(fmt=fmt, datefmt="%Y-%m-%d %H:%M:%S")

    def _create_json_formatter(self) -> logging.Formatter:
        """
        Create a JSON-based log formatter.

        If python-json-logger is not installed, it falls back to the text formatter.

        :return: A JSON-based log formatter.
        :rtype: logging.Formatter
        """
        try:
            from pythonjsonlogger import jsonlogger
        except ImportError:
            self._logger.warning(
                "python-json-logger not installed, falling back to text format"
            )
            return self._create_text_formatter(colorized=False)

        class CustomJsonFormatter(jsonlogger.JsonFormatter):
            def add_fields(self, log_record, record, message_dict):
                super().add_fields(log_record, record, message_dict)
                log_record["timestamp"] = datetime.utcnow().isoformat()
                log_record["level"] = record.levelname
                log_record["logger"] = record.name
                log_record["module"] = record.module
                if record.levelno == logging.DEBUG:
                    log_record["file"] = f"{record.filename}:{record.lineno}"
                    log_record["function"] = record.funcName

        return CustomJsonFormatter(
            "%(timestamp)s %(level)s %(logger)s %(module)s %(file)s %(function)s %(message)s"
        )


def configure_logging(
    level: LogLevel = LogLevel.INFO,
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    json_format: bool = False,
    colorize: bool = True,
) -> logging.Logger:
    """
    Configure application logging with enhanced features.

    Args:
        level: Minimum logging level (default: INFO)
        log_file: Path to log file (optional)
        max_bytes: Maximum log file size before rotation (default: 10MB)
        backup_count: Number of backup logs to keep (default: 5)
        json_format: Whether to use JSON formatting (default: False)
        colorize: Whether to colorize console output (default: True)

    Returns:
        Configured logger instance
    """
    logger = FastAPILogger(
        level=level,
        log_file=log_file,
        max_bytes=max_bytes,
        backup_count=backup_count,
        json_format=json_format,
        colorize=colorize,
    ).logger

    # Capture warnings from the warnings module
    logging.captureWarnings(True)

    return logger
