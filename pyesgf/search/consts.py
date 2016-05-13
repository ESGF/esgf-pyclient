#-----------------------------------------------------------------------------
# Constants

TYPE_DATASET = 'Dataset'
TYPE_FILE = 'File'
TYPE_AGGREGATION = 'Aggregation'
QUERY_KEYWORD_TYPES = ('system', 'facet', 'freetext', 'temporal', 'geospatial')
RESPONSE_FORMAT='application/solr+json'
DEFAULT_BATCH_SIZE = 50

OPERATOR_NEQ = 'not_equal'

SHARD_REXP = r'^(?P<prefix>https?://)?(?P<host>.+?):?(?P<port>\d+)?/(?P<suffix>.*)$'

