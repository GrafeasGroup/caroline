import logging

from jsonschema import validate

from caroline.config import config
from caroline.databases.elasticsearch import elasticsearch_db
from caroline.databases.redis import redis_db
from caroline.errors import CarolineConfigurationError

log = logging.getLogger(__name__)


def validate_config():
    if config.default_db not in ["redis", "elasticsearch"]:
        raise CarolineConfigurationError(
            "Default DB has been changed to invalid option; use either "
            '"elasticsearch" or "redis"'
        )


class Base(object):
    """
    Welcome to the weirdness that is Caroline.

    Caroline is a ODM that specializes in all things json, because
    frankly I really don't like working with ORMs and the way that they're
    normally handled in Python (thanks, Django!).

    It's very simple: you create a class using a minimum of two objects:

      * A dict of what you want your data to look like
      * a dict of valid jsonschema that will be used to validate your data
          on save

    That's it. No models, no craziness, minor setup time, and hopefully pretty
    simple to use. That's the goal, anyways.

    Why Caroline? Because we can. Also, here's a song list of tracks you may
    or may not already be familiar with, arranged by release year!

    * Caroline - Steep Canyon Rangers (2017)
    * Caroline I See You - James Taylor (2002)
    * Caroline - Fleetwood Mac (1987)
    * Oh Caroline - Cheap Trick (1977)
    * Sweet Caroline - Neil Diamond (1965)
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
        Why else use a library like Caroline?

        Because the user creates the class with those variables defined,
        we can structure the parent around them. Fun!
        """
        # First things first! What DB are we using? Gonna do this the long
        # way for legibility purposes and because the hasattr call is not
        # expensive.
        db_map = {"elasticsearch": elasticsearch_db, "redis": redis_db}

        if hasattr(self, "redis_conn") and hasattr(self, "elasticsearch_conn"):
            raise CarolineConfigurationError(
                "Received both a Redis connection and an Elasticsearch connection. "
                "You need to use one or the other -- Caroline does not support "
                "handling both at the same time."
            )

        if hasattr(self, "redis_conn"):
            self.db = redis_db(self.redis_conn)

        if hasattr(self, "elasticsearch_conn"):
            self.db = elasticsearch_db(self.elasticsearch_conn)

        if not hasattr(self, "db"):
            try:
                self.db = db_map[config.default_db]()
            except KeyError:
                raise CarolineConfigurationError(
                    "Did not receive db connection in model and environment variable "
                    "points towards an invalid location. "
                    "Valid connections are: {}".format(", ".join([x for x in db_map]))
                )

        if isinstance(self.db, str):
            if self.db in db_map:
                log.debug(f"Overriding defaults with requested db base {self.db}")
                self.db = db_map[self.db]()
            else:
                raise CarolineConfigurationError(
                    "The requested db {} is not available as an option. Usable "
                    "options are: {}".format(self.db, ", ".join([x for x in db_map]))
                )

        if not hasattr(self, "default"):
            log.warning(
                "Did not receive a default dict; no default attributes will be "
                "applied to the model {}. Please define a `default` attribute "
                "on your model in order for values to be assigned appropriately "
                "on creation.".format(self.__class__.__name__)
            )
            self.default = {}

        if not isinstance(self.default, dict):
            raise CarolineConfigurationError("default must be a dict!")

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

    def __delitem__(self, key):
        del self.data[key]

    def get(self, key, default_return=None):
        return self.data.get(key, default_return)

    def _load(self, requested_key):
        """
        :return: Dict or None; the loaded information from the db.
        """
        return self.db.load(scope=self, key=requested_key)

    def save(self):
        if self.validate():
            self.db.save(scope=self)

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

    def upgrade(self):
        """
        Use this when you've got existing keys in your db and you need to change
        the defaults and the schema. This will merge the new fields with the
        default values set in the model every time a key is loaded.
        Upgrade-as-you-go, if you will.

        :return: None
        """
        # first we add in all the new fields that may have been set in the default
        # dict
        for key in self.default:
            if key in self.to_dict():
                continue
            self.update(key, self.default[key])

        # now we nuke any additional fields that may have been removed from the
        # default dict.
        keys_to_remove = list()

        for key in self.to_dict():
            if key not in self.default:
                keys_to_remove.append(key)

        if len(keys_to_remove) > 0:
            for k in keys_to_remove:
                del self[k]

    def all_keys(self):
        # returns a generator that the developer can handle how they wish -- this
        # will return all of the keys matching this model type currently stored in
        # the db. Currently only works when using the Redis connection.
        return self.db.all_keys(self)
