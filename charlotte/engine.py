import json
import logging
import os

import redis
from jsonschema import validate
import elasticsearch
from elasticsearch import Elasticsearch
from addict import Dict

from charlotte.errors import CharlotteConfigurationError
from charlotte.errors import CharlotteConnectionError

log = logging.getLogger(__name__)

config = Dict()
config.default_db = "elasticsearch"
config.redis_default_url = "redis://localhost:6379/0"
# TODO: accept additional config vars for elasticsearch besides just URL
config.elasticsearch_default_url = "localhost:9200"

# we don't actually connect to redis until we use the object; putting it here
# means that we have the connection pool available if we need it.
# Let's see if we have a Redis environment variable set!
redis_env_addr = os.environ.get("CHARLOTTE_REDIS_URL", config.redis_default_url)
pool = redis.ConnectionPool.from_url(redis_env_addr)

# While we're at it, Elasticsearch doesn't use connection pools the same way
# that Redis does, so we'll set up the client here and have all the active ES
# models use it. We won't check to see if it's actually valid unless it's called.
es_env_addr = os.environ.get(
    "CHARLOTTE_ELASTICSEARCH_URL", config.elasticsearch_default_url
)
es_charlotte_connection = Elasticsearch(es_env_addr)


def validate_config():
    if config.default_db not in ["redis", "elasticsearch"]:
        raise CharlotteConfigurationError(
            "Default DB has been changed to invalid option; use either "
            '"elasticsearch" or "redis"'
        )


class redis_db(object):
    def __init__(self, redis_conn=None):
        try:
            if redis_conn:
                # We have something -- we'll run it through the same testing code to
                # make sure that it works.
                self.r = redis_conn
            else:
                self.r = redis.Redis(connection_pool=pool)
            self.r.ping()
        except redis.exceptions.ConnectionError:
            raise CharlotteConnectionError("Unable to reach Redis.")
        except Exception as e:
            raise CharlotteConfigurationError(
                "Caught {} -- please pass in an instantiated Redis "
                "connection.".format(e)
            )

    def load(self, scope, key):
        """
        :return: Dict or None; the loaded information from Redis.
        """
        result = self.r.get(scope.db_key.format(key))
        if not result:
            log.debug("Key {} not found, returning None.".format(key))
            return None

        return json.loads(result.decode())

    def save(self, scope):
        self.r.set(scope.db_key.format(scope.id), json.dumps(scope.data))


class elasticsearch_db(object):
    def __init__(self, es_conn=None):
        try:
            if es_conn:
                self.es = es_conn
            else:
                # we didn't get anything, so we'll piggyback off of the connection
                # that charlotte creates
                self.es = es_charlotte_connection
            log.info("Trying to connect to Elasticsearch...")
            self.es.info()
            log.info("Connection complete!")
        except elasticsearch.exceptions.ConnectionError:
            # Elasticsearch client raises _a lot_ of nested errors in this instance.
            # Nuke them all with extreme prejudice.
            raise CharlotteConnectionError(
                "Cannot reach Elasticsearch! Is it running?"
            ) from None

    def load(self, scope, key):
        pass

    def save(self, scope):
        pass


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

    def __init__(self, id):
        """
        Everything that we should need is passed in by the user and found
        under the `self` object. Here's what we should be seeing:

        class User(Prototype):
            default_structure = {valid dict}

            # optional flags
            schema = {valid jsonschema}
            db_key = "user-obj"

            redis_conn = r
            OR
            elasticsearch_conn = e

        The schema is technically optional, but we want people to use it.
        Why else use a library like Charlotte?

        Because the user creates the class with those variables defined,
        we can structure the parent around them. Fun!
        """
        # First things first! What DB are we using? Gonna do this the long
        # way for legibility purposes and because the hasattr call is not
        # expensive.
        if hasattr(self, "redis_conn") and hasattr(self, "elasticsearch_conn"):
            raise CharlotteConfigurationError(
                "Received both a Redis connection and an Elasticsearch connection. "
                "You need to use one or the other -- Charlotte does not support "
                "handling both at the same time."
            )

        if hasattr(self, "redis_conn"):
            self.db = redis_db(self.redis_conn)

        if hasattr(self, "elasticsearch_conn"):
            self.db = elasticsearch_db(self.elasticsearch_conn)

        if not hasattr(self, "db"):
            log.debug("No db connection passed; defaulting to Elasticsearch")
            self.db = elasticsearch_db()

        if not hasattr(self, "default_structure"):
            raise CharlotteConfigurationError(
                "Must have a default_structure dict, even if it's just {}!"
            )
        if type(self.default_structure) != dict:
            raise CharlotteConfigurationError("default_structure must be a dict!")

        if not hasattr(self, "db_key"):
            # if we don't have a db_key passed in, then we use the name of the
            # class that the developer defined as the key.
            self.db_key = self.__class__.__name__.lower()
            log.debug('No db_key passed; defaulting to key "{}"'.format(self.db_key))
        else:
            self.db_key = str(self.db_key)
        # note: this is a way of allowing us to only format the first field.
        # It'll render out as "::thing::{}" which we can then format again.
        self.db_key = "::{}::{{}}".format(self.db_key)

        if not hasattr(self, "schema"):
            self.schema = None

        self.id = id

        result = self._load(self.id)
        if result:
            self.data = result
        else:
            self.data = self.default_structure

    def __repr__(self):
        return repr(self.data)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    def get(self, key, default_return=None):
        return self.data.get(key, default_return)

    def _load(self, requested_key):
        """
        :return: Dict or None; the loaded information from the db.
        """
        return self.db.load(self, requested_key)

    def save(self):
        if self.validate():
            self.db.save(self)

    def update(self, key, value):
        self.data[key] = value

    def to_dict(self):
        return self.data

    def validate(self):
        # validate will return None if it succeeds or throw an exception, so if
        # we get to the return statement then we're good.
        # Alternatively, they can just not give us a schema -- in which case,
        # just return True and don't sweat it.
        if self.schema:
            validate(self.data, self.schema)
        return True
