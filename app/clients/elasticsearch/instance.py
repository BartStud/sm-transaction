from elasticsearch import AsyncElasticsearch

from app.core.config import ELASTICSEARCH_HOST


def get_es_instance():
    return AsyncElasticsearch(hosts=[ELASTICSEARCH_HOST])
