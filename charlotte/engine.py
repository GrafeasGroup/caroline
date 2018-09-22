import logging

from jsonschema import validate

from charlotte.config import config
from charlotte.databases.elasticsearch import elasticsearch_db
from charlotte.databases.redis import redis_db
from charlotte.errors import CharlotteConfigurationError

log = logging.getLogger(__name__)


def validate_config():
    if config.default_db not in ["redis", "elasticsearch"]:
        raise CharlotteConfigurationError(
            "Default DB has been changed to invalid option; use either "
            '"elasticsearch" or "redis"'
        )


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

    def __init__(self, record_id):
        """
        Everything that we should need is passed in by the user and found
        under the `self` object. Here's what we should be seeing:

        class User(Prototype):
            default = {valid dict}

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

        if not hasattr(self, "default"):
            raise CharlotteConfigurationError(
                "Must have a default dict, even if it's just {}!"
            )

        if not isinstance(self.default, dict):
            raise CharlotteConfigurationError("default must be a dict!")

        if not hasattr(self, "db_key"):
            # if we don't have a db_key passed in, then we use the name of the
            # class that the developer defined as the key.
            self.db_key = self.__class__.__name__.lower()
            log.debug('No db_key passed; defaulting to key "{}"'.format(self.db_key))
        else:
            self.db_key = str(self.db_key)
        # back up the original key in case we're using elasticsearch so that we can
        # use it for the object type.
        self.db_key_unformatted = self.db_key
        # note: this is a way of allowing us to only format the first field.
        # It'll render out as "::thing::{}" which we can then format again.
        self.db_key = "::{}::{{}}".format(self.db_key)

        if not hasattr(self, "schema"):
            self.schema = None

        self.record_id = record_id

        result = self._load(self.record_id)
        if result:
            self.data = result
        else:
            self.data = self.default

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
        # yes, we're passing the scope. You're not reading it wrong.
        return self.db.load(self, requested_key)

    def save(self):
        if self.validate():
            # yep, passing scope again
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

    def all_keys(self):
        # returns a generator from the redis library that the developer can
        # handle how they wish -- this will return all of the keys matching
        # this model type currently stored in Redis.
        return self.db.all_keys(self)
