import logging
import structlog
from pathlib import Path
from logging.handlers import RotatingFileHandler
from rich.console import Console
from rich.logging import RichHandler
from recon.config.settings import Settings

def setup_logging(settings: Settings) -> None:
    """Configure structlog with console and file outputs."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Shared processors
    timestamper = structlog.processors.TimeStamper(fmt="iso")
    pre_chain = [
        structlog.stdlib.add_log_level,
        timestamper,
    ]

    # Console handler with Rich
    console_handler = RichHandler(
        console=Console(stderr=True),
        show_time=False,
        show_path=False,
        rich_tracebacks=True,
        markup=True,
    )
    console_handler.setLevel(log_level)

    # File handler with rotation
    log_dir = settings.log_file_dir
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_dir / "recon.log", maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    # File handler uses plain text with JSON optional
    if settings.log_format == "json":
        file_formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer()
        )
    else:
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
    file_handler.setFormatter(file_formatter)

    # Configure stdlib logging
    logging.basicConfig(level=log_level, handlers=[console_handler, file_handler])

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            *pre_chain,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )