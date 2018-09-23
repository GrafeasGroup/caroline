import logging

from charlotte.config import config
from charlotte.engine import Base as Prototype
from charlotte.errors import *

name = "charlotte"

__all__ = [
    "Prototype",
    "CharlotteConfigurationError",
    "CharlotteConnectionError",
    "config",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())
