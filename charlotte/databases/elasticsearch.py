import os

import logging

import elasticsearch
from elasticsearch import Elasticsearch

from charlotte.config import es_env_addr
from charlotte.errors import CharlotteConnectionError

log = logging.getLogger(__name__)

# While we're at it, Elasticsearch doesn't use connection pools the same way
# that Redis does, so we'll set up the client here and have all the active ES
# models use it. We won't check to see if it's actually valid unless it's called.
es_charlotte_connection = Elasticsearch(es_env_addr)


class elasticsearch_db(object):
    def __init__(self, es_conn=None):
        try:
            if es_conn:
                self.es = es_conn
            else:
                # we didn't get anything, so we'll piggyback off of the connection
                # that charlotte creates
                self.es = es_charlotte_connection
            log.debug("Trying to connect to Elasticsearch...")
            self.es.info()
            log.debug("Connection complete!")
        except elasticsearch.exceptions.ConnectionError:
            # Elasticsearch client raises _a lot_ of nested errors in this instance.
            # Nuke them all with extreme prejudice.
            raise CharlotteConnectionError(
                "Cannot reach Elasticsearch! Is it running?"
            ) from None

    def load(self, scope, key):
        try:
            result = self.es.get(
                index="charlotte", doc_type=scope.db_key_unformatted, id=key
            )
            # we don't need the whole response from ElasticSearch; we only need the
            # body that we set.
            result = result.get("_source")
        except elasticsearch.exceptions.NotFoundError:
            log.debug("ES key {} not found, returning None.".format(key))
            result = None
        return result

    def save(self, scope):
        self.es.index(
            index="charlotte",
            doc_type=scope.db_key_unformatted,
            id=scope.record_id,
            body=scope.to_dict(),
        )

    def all_keys(self, scope):
        raise NotImplementedError(
            "This is only valid for Redis databases at the moment."
        )
