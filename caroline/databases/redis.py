import json
import logging

import redis

from caroline.config import redis_env_addr
from caroline.errors import CarolineConfigurationError
from caroline.errors import CarolineConnectionError

log = logging.getLogger(__name__)

# we don't actually connect to redis until we use the object; putting it here
# means that we have the connection pool available if we need it.
# Let's see if we have a Redis environment variable set!
pool = redis.ConnectionPool.from_url(redis_env_addr)


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
            raise CarolineConnectionError("Unable to reach Redis.")
        except Exception as e:
            raise CarolineConfigurationError(
                "Caught {} -- please pass in an instantiated Redis "
                "connection.".format(e)
            )

    def load(self, scope, key):
        """
        :return: Dict or None; the loaded information from Redis.
        """
        result = self.r.get(scope.db_key.format(key))
        if not result:
            log.debug("Redis key {} not found, returning None.".format(key))
            return None

        return json.loads(result.decode())

    def save(self, scope):
        self.r.set(scope.db_key.format(scope.record_id), json.dumps(scope.data))

    def all_keys(self, scope):
        return self.r.scan_iter("{}*".format(scope.db_key))
