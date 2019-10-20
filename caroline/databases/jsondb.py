import json
import logging
import os

from caroline.errors import CarolineConfigurationError
from caroline.errors import CarolineConnectionError

log = logging.getLogger(__name__)


class json_db(object):
    name = "JSON simple DB"

    def __init__(self, path):
        self.path = path
        if os.path.exists(path):
            with open(path) as f:
                try:
                    self.data = json.load(f)
                except json.decoder.JSONDecodeError:
                    # It looks like the file is there, but it's empty.
                    self.data = {}
        else:
            self.data = {}

    def load(self, scope, key):
        result = self.data.get(scope.db_key.format(key))
        if not result:
            log.debug("Key {} not found, returning None.".format(key))
            return None

        return result

    def save(self, scope):
        self.data[scope.db_key.format(scope.record_id)] = scope.data
        with open(self.path, "w") as f:
            f.write(json.dumps(self.data, indent=2, sort_keys=True))

    def all_keys(self, scope):
        return self.data.keys()
