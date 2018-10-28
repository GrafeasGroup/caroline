import os

from addict import Dict

config = Dict()

config.default_db = os.environ.get("CAROLINE_DEFAULT_DB", "elasticsearch")
config.connection_timeout = os.environ.get("CAROLINE_CONNECTION_TIMEOUT", 0.01)

config.redis_default_url = "redis://localhost:6379/0"

# TODO: accept additional config vars for elasticsearch besides just URL
config.elasticsearch_default_url = "localhost:9200"


redis_env_addr = os.environ.get("CAROLINE_REDIS_URL", config.redis_default_url)
es_env_addr = os.environ.get(
    "CAROLINE_ELASTICSEARCH_URL", config.elasticsearch_default_url
)
