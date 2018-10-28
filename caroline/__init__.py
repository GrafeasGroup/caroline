import logging

from caroline.config import config
from caroline.engine import Base as Prototype
from caroline.errors import *

name = "caroline"

__all__ = [
    "Prototype",
    "CarolineConfigurationError",
    "CarolineConnectionError",
    "config",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())
