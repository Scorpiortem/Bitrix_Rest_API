import logging
import sys
from pathlib import Path
import os

def setup_logger(config: dict) -> logging.Logger:
    logger = logging.getLogger("deal_dossier")
    logger.setLevel(config.get("log_level", "INFO"))

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    log_path = config.get("log_path")
    if log_path:
        try:
            log_dir = Path(log_path)
            log_dir.mkdir(parents=True, exist_ok=True)

            # Проверка доступности директории для записи
            if log_dir.is_dir() and os.access(log_dir, os.W_OK):
                log_file = log_dir / "app.log"
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            else:
                logger.warning(f"Cannot write to log directory: {log_dir}")
        except Exception as e:
            logger.warning(f"Failed to setup file logging: {e}")

    return logger
