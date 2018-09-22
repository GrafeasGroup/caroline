from unittest.mock import patch

# noinspection PyUnresolvedReferences
import redis
import pytest

from charlotte.engine import Base
from charlotte.errors import CharlotteConfigurationError


@patch("redis.Redis")
@patch("charlotte.engine.Base._load", return_value={"hello": "world"})
def test_generic_launch(a, b):
    class x(Base):
        default_structure = {}

    y = x("asdf")
    assert y.to_dict() == {"hello": "world"}


@patch("redis.Redis")
@patch("charlotte.engine.Base._load", return_value=None)
def test_default_structure_loading(a, b):
    class x(Base):
        default_structure = {"yo": "world"}

    y = x("asdf")
    # asdf didn't come back with anything because _load failed, so it should
    # be the default structure.
    assert y.to_dict() == {"yo": "world"}


@patch("redis.Redis")
@patch("charlotte.engine.Base._load", return_value=None)
def test_redis_key_var(a, b):
    class x(Base):
        default_structure = {"yo": "world"}
        db_key = "snarfleblat"

    y = x("asdf")

    assert y.redis_key == "::snarfleblat::{}"


@patch("redis.Redis")
@patch("charlotte.engine.Base._load", return_value=None)
def test_update_methods(a, b):
    class x(Base):
        default_structure = {"yo": "world"}

    y = x("asdf")

    assert y.to_dict() == {"yo": "world"}
    y.update("yo", "hello there")
    assert y.to_dict() == {"yo": "hello there"}
    y["yo"] = "general kenobi"
    assert y.to_dict() == {"yo": "general kenobi"}


@patch("redis.Redis")
def test_required_default_structure(a):
    with pytest.raises(CharlotteConfigurationError):

        class x(Base):
            pass

        y = x("asdf")
