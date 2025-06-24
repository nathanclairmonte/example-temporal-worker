import logging
import os
from functools import lru_cache

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


@lru_cache
def read_config():
    """
    Read configuration variables.
    """
    load_dotenv(".env.local")

    return {
        "logging_level": os.getenv("LOGGING_LEVEL", "INFO").lower(),
        "temporal": {"server_url": os.getenv("TEMPORAL_HOST")},
    }
