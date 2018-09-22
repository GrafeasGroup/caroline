import os

from addict import Dict

config = Dict()
config.default_db = "elasticsearch"
config.redis_default_url = "redis://localhost:6379/0"
# TODO: accept additional config vars for elasticsearch besides just URL
config.elasticsearch_default_url = "localhost:9200"

redis_env_addr = os.environ.get("CHARLOTTE_REDIS_URL", config.redis_default_url)
es_env_addr = os.environ.get(
    "CHARLOTTE_ELASTICSEARCH_URL", config.elasticsearch_default_url
)