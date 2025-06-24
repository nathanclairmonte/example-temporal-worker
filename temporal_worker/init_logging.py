import logging

from temporal_worker.config import read_config


def init_logging():
    logging_levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
    }

    config = read_config()
    logging_level_name: str = config["logging_level"]
    logging_level = logging_levels.get(logging_level_name, logging.INFO)

    log_format = "%(asctime)s.%(msecs)03d %(levelname)-8s %(name)s %(message)s"

    logging.basicConfig(
        level=logging_level,
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger = logging.getLogger(__name__)
    logger.info(f"initialized logging ({logging_level_name.upper()})")
