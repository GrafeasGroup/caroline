import logging

import elasticsearch
from elasticsearch import Elasticsearch

from caroline.config import config
from caroline.config import es_env_addr
from caroline.errors import CarolineConnectionError

log = logging.getLogger(__name__)

# While we're at it, Elasticsearch doesn't use connection pools the same way
# that Redis does, so we'll set up the client here and have all the active ES
# models use it. We won't check to see if it's actually valid unless it's called.

# The timeout is also set extremely low because otherwise the library will hang
# if elasticsearch is not running; for a system that uses Redis only, then we want
# it to fail quickly if a connection is not immediately detected. This can be
# adjusted by changing the environment variable `CAROLINE_CONNECTION_TIMEOUT`.
es_caroline_connector = Elasticsearch(
    es_env_addr, timeout=config.connection_timeout, max_retries=0
)


class elasticsearch_db(object):
    def __init__(self, es_conn=None):
        try:
            if es_conn:
                self.es = es_conn
            else:
                # we didn't get anything, so we'll piggyback off of the connection
                # that caroline creates
                self.es = es_caroline_connector
            log.debug("Trying to connect to Elasticsearch...")
            self.es.info()
            log.debug("Connection complete!")
        except elasticsearch.exceptions.ConnectionError:
            # Elasticsearch client raises _a lot_ of nested errors in this instance.
            # Nuke them all with extreme prejudice.
            raise CarolineConnectionError(
                "Cannot reach Elasticsearch! Is it running?"
            ) from None

    def load(self, scope, key):
        try:
            result = self.es.get(
                index="caroline", doc_type=scope.db_key_unformatted, id=key
            )
            # we don't need the whole response from Elasticsearch; we only need the
            # body that we set.
            result = result.get("_source")
        except elasticsearch.exceptions.NotFoundError:
            log.debug("ES key {} not found, returning None.".format(key))
            result = None
        return result

    def save(self, scope):
        self.es.index(
            index="caroline",
            doc_type=scope.db_key_unformatted,
            id=scope.record_id,
            body=scope.to_dict(),
        )

    def all_keys(self, scope):
        raise NotImplementedError(
            "This is only valid for Redis databases at the moment."
        )
