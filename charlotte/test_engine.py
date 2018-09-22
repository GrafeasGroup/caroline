from unittest.mock import MagicMock
from unittest.mock import patch

# noinspection PyUnresolvedReferences
import elasticsearch
import pytest

# noinspection PyUnresolvedReferences
import redis

from charlotte.engine import Base
from charlotte.errors import CharlotteConfigurationError


@patch("charlotte.engine.Base._load", return_value={"hello": "world"})
def test_generic_launch(a):
    class x(Base):
        redis_conn = MagicMock()
        default = {}

    y = x("asdf")
    assert y.to_dict() == {"hello": "world"}


@patch("charlotte.engine.Base._load", return_value=None)
def test_default_loading(a):
    class x(Base):
        redis_conn = MagicMock()
        default = {"yo": "world"}

    y = x("asdf")
    # asdf didn't come back with anything because _load failed, so it should
    # be the default structure.
    assert y.to_dict() == {"yo": "world"}


@patch("charlotte.engine.Base._load", return_value=None)
def test_redis_key_var(a):
    class x(Base):
        redis_conn = MagicMock()
        default = {"yo": "world"}
        db_key = "snarfleblat"

    y = x("asdf")

    assert y.db_key == "::snarfleblat::{}"
    assert y.db_key_unformatted == "snarfleblat"


@patch("charlotte.engine.Base._load", return_value=None)
def test_update_methods(a):
    class x(Base):
        redis_conn = MagicMock()
        default = {"yo": "world"}

    y = x("asdf")

    assert y.to_dict() == {"yo": "world"}
    y.update("yo", "hello there")
    assert y.to_dict() == {"yo": "hello there"}
    y["yo"] = "general kenobi"
    assert y.to_dict() == {"yo": "general kenobi"}


def test_required_default():
    with pytest.raises(CharlotteConfigurationError):

        class x(Base):
            redis_conn = MagicMock()

        y = x("asdf")


def test_multiple_dbs_configured():
    with pytest.raises(CharlotteConfigurationError):

        class x(Base):
            redis_conn = MagicMock()
            es_conn = MagicMock()

        y = x("asdf")
