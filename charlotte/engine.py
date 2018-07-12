import json
import logging
import os

import redis
from jsonschema import validate

try:
    import better_exceptions

    better_exceptions.MAX_LENGTH = None
except ImportError:
    pass

from charlotte.errors import CharlotteConnectionError


class Base(object):
    """
    TODO: add general ideas of how this works
    """

    def __init__(self, redis_conn=None):
        """
        Create our own Redis connection if one is not passed in.
        We also assume that there is already a logging object created.

        :param redis: Object; a `redis` instance.
        """
        super().__init__()
        if redis_conn:
            self.r = redis_conn
        else:
            try:
                url = os.getenv("REDIS_CONNECTION_URL", "redis://localhost:6379/0")
                self.r = redis.StrictRedis.from_url(url)
                self.r.ping()
            except redis.exceptions.ConnectionError:
                raise CharlotteConnectionError("Unable to reach Redis.")

        # self.create_if_not_found = create_if_not_found
        # self.redis_key = '::user::{}'
        self.redis_key = None
        # self.user_data = self._load()
        self.data = dict()
        self.schema = None

    def __repr__(self):
        return repr(self.data)

    def get(self, key, default_return=None):
        return self.data.get(key, default_return)

    def _load(self, requested_key):
        """
        :return: Dict or None; the loaded information from Redis.
        """
        result = self.r.get(self.redis_key.format(requested_key))
        if not result:
            logging.debug("Key {} not found, returning None.".format(requested_key))
            return None

        return json.loads(result.decode())

    def save(self, keyname):
        if self.validate():
            self.r.set(self.redis_key.format(keyname), json.dumps(self.data))

    def update(self, key, value):
        self.data[key] = value

    def _create_default_data(self):
        self.data = dict()
        self.data.update({"username": self.username})
        return self.data

    def to_dict(self):
        return self.data

    def validate(self):
        return validate(self.data, self.schema)
