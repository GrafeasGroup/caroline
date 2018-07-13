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
from charlotte.errors import CharlotteConfigurationError


class Base(object):
    """
    Welcome to the weirdness that is Charlotte.

    Charlotte is a ODM that specializes in all things json, because
    frankly I really don't like working with ORMs and the way that they're
    normally handled in Python (thanks, Django!).

    It's very simple: you create a class using a minimum of two objects:

      * A dict of what you want your data to look like
      * a dict of valid jsonschema that will be used to validate your data
          on save

    That's it. No models, no craziness, minor setup time, and hopefully pretty
    simple to use. That's the goal, anyways.

    Why Charlotte? I like Charlotte best. Because it's good. Good Charlotte.
    """

    def __init__(self):
        """
        Everything that we should need is passed in by the user and found
        under the `self` object. Here's what we should be seeing:

        class User(Prototype):
            schema = {valid jsonschema}
            default_structure = {valid dict}
            # optional
            redis_object = r

        Because the user creates the class with those variables defined,
        we can structure the parent around them. Fun!
        """
        import pdb

        pdb.set_trace()
        try:
            if hasattr(self, "redis_conn"):
                # We have something -- we'll run it through the same testing code to
                # make sure that it works.
                self.r = self.redis_conn
            else:
                url = os.getenv("REDIS_CONNECTION_URL", "redis://localhost:6379/0")
                self.r = redis.StrictRedis.from_url(url)
            self.r.ping()
        except redis.exceptions.ConnectionError:
            raise CharlotteConnectionError("Unable to reach Redis.")
        except Exception as e:
            raise CharlotteConfigurationError(
                "Caught {} -- please pass in an instantiated Redis connection.".format(
                    e
                )
            )

        if not hasattr(self, "default_structure"):
            raise CharlotteConfigurationError
        if not hasattr(self, "redis_key"):
            self.redis_key = "::{}::{{}}".format(self.__class__.__name__.lower())
        self.data = self.default_structure
        if not hasattr(self, 'schema'):
            self.schema = dict()

    def __repr__(self):
        return repr(self.data)

    def get(self, key, default_return=None):
        return self.data.get(key, default_return)

    def load(self, requested_key):
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
