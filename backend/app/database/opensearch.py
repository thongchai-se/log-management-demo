from opensearchpy import OpenSearch
from app.config import OPENSEARCH_HOST, OPENSEARCH_PORT

client = OpenSearch(
    hosts=[
        {
            "host": OPENSEARCH_HOST,
            "port": OPENSEARCH_PORT,
        }
    ]
)