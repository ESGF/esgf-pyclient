"""

Module :mod:`pyesgf.search.results`
===================================

Search results are retrieved through the :class:`ResultSet` class.  This class
hides paging of large result sets behind a client-side cache.  Subclasses of 
:class:`Result` represent results of different SOLr record type.

"""

from collections import Sequence, defaultdict
import re

from .consts import (DEFAULT_BATCH_SIZE, TYPE_DATASET, TYPE_FILE, 
                     TYPE_AGGREGATION)
from .exceptions import EsgfSearchException

class ResultSet(Sequence):
    """
    :ivar context: The search context object used to generate this resultset
    :property batch_size: The number of results that will be requested
        from esgf-search as one call.  This must be set on creation and
        cannot change.

    """
    def __init__(self, context, batch_size=DEFAULT_BATCH_SIZE, eager=True):
        """
        :param context: The search context object used to generate this resultset
        :param batch_size: The number of results that will be requested from
            esgf-search as one call.
        :param eager: Boolean specifying whether to retrieve the first batch on
            instantiation.
            
        """
        self.context = context
        self.__batch_size = batch_size
        self.__batch_cache = [None] * ((len(self) / batch_size) + 1)
        if eager and len(self)>0:
            self.__batch_cache[0] = self.__get_batch(0)

    def __getitem__(self, index):
        batch_i = index / self.batch_size
        offset = index % self.batch_size
        if self.__batch_cache[batch_i] is None:
            self.__batch_cache[batch_i] = self.__get_batch(batch_i)
        batch = self.__batch_cache[batch_i]

        search_type = self.context.search_type
        ResultClass = _result_classes[search_type]

        #!TODO: should probably wrap the json inside self.__batch_cache
        return ResultClass(batch[offset], self.context)
            

    def __len__(self):
        return self.context.hit_count

    @property
    def batch_size(self):
        return self.__batch_size

    def _build_result(self, result):
        """
        Construct a result object from the raw json.

        This method is designed to be overridden in subclasses if desired.
        The default implementation simply returns the json.
        
        """
        return result

    def __get_batch(self, batch_i):
        offset = self.batch_size * batch_i
        limit = self.batch_size

        query_dict = self.context._build_query()
        response = self.context.connection.send_search(query_dict, limit=limit, 
                                                       offset=offset,
                                                       shards=self.context.shards)
        
        #!TODO: strip out results
        return response['response']['docs']


class BaseResult(object):
    """
    Base class for results.

    Subclasses represent different search types such as File and Dataset.

    :ivar json: The oroginial json representation of the result.
    :ivar context: The SearchContext which generated this result.
    :property urls: a dictionary of the form {service: [(url, mime_type), ...], ...}
    :property opendap_url: The url of an OPeNDAP endpoint for this result if available
    :property las_url: The url of an LAS endpoint for this result if available
    :property download_url: The url for downloading the result by HTTP if available
    :property gridftp_url: The url for downloading the result by Globus if available
    :property index_node: The index node from where the metadata is stored.  
        Calls to *_context() will optimise queries to only address this node.

    """
    def __init__(self, json, context):
        self.json = json
        self.context = context
        
    @property
    def urls(self):
        url_dict = defaultdict(list)
        for encoded in self.json['url']:
            url, mime_type, service = encoded.split('|')
            url_dict[service].append((url, mime_type))

        return url_dict

    @property
    def opendap_url(self):
        try:
            url, mime = self.urls['OPENDAP'][0]
        except (KeyError, IndexError):
            return None
        
        url = re.sub(r'.html$', '', url)

        return url

    @property
    def las_url(self):
        try:
            url, mime = self.urls['LAS'][0]
        except (KeyError, IndexError):
            return None

        return url

    @property
    def download_url(self):
        try:
            url, mime = self.urls['HTTPServer'][0]
        except (KeyError, IndexError):
            return None

        return url

    @property
    def gridftp_url(self):
        try:
            url, mime = self.urls['GridFTP'][0]
        except (KeyError, IndexError):
            return None

        return url

    @property
    def index_node(self):
        try:
            index_node = self.json['index_node']
        except KeyError:
            return None

        return index_node


class DatasetResult(BaseResult):
    """
    A result object for ESGF datasets.

    :property dataset_id: The solr dataset_id which is unique throughout the system.

    """

    @property
    def dataset_id(self):
        #!TODO: should we decode this into a tuple?  self.json['id'].split('|')
        return self.json['id']
    
    @property
    def number_of_files(self):
        """
        Returns file count as reported by the dataset record.
        """
        return self.json['number_of_files']

    def file_context(self):
        """
        Return a SearchContext for searching for files within this dataset.
        """
        from .context import FileSearchContext

        if self.context.connection.distrib:
            # If the index node is in the available shards for this connection then
            # restrict shards to that node.  Otherwise do nothing to handle the case
            # when the shard is replicated
            available_shards = self.context.connection.get_shard_list().keys()
            if self.index_node in available_shards:
                shards = [self.index_node]
            else:
                shards = None
        else:
            shards = None

        files_context = FileSearchContext(
            connection=self.context.connection,
            constraints={'dataset_id': self.dataset_id},
            shards=shards,
            )
        return files_context

    def aggregation_context(self):
        """
        Return a SearchContext for searching for aggregations within this dataset.
        """
        from .context import AggregationSearchContext

        if self.context.connection.distrib:
            # If the index node is in the available shards for this connection then
            # restrict shards to that node.  Otherwise do nothing to handle the case
            # when the shard is replicated
            available_shards = self.context.connection.get_shard_list().keys()
            if self.index_node in available_shards:
                shards = [self.index_node]
            else:
                shards = None
        else:
            shards = None

        agg_context = AggregationSearchContext(
            connection=self.context.connection,
            constraints={'dataset_id': self.dataset_id},
            shards=shards,
            )
        return agg_context

class FileResult(BaseResult):
    """
    A result object for ESGF files.  Properties from :class:`BaseResult` are inherited.

    :property file_id: The identifier for the file
    :property checksum: The checksum of the file
    :property checksum_type: The algorithm used for generating the checksum
    :property filename: The filename
    :proprty size: The file size in bytes

    """
    @property
    def file_id(self):
        return self.json['id']

    @property
    def checksum(self):
        try:
            return self.json['checksum'][0]
        except KeyError:
            return None

    @property
    def checksum_type(self):
        try:
            return self.json['checksum_type'][0]
        except KeyError:
            return None

    @property
    def filename(self):
        return self.json['title']

    @property
    def size(self):
        return int(self.json['size'])

    @property
    def tracking_id(self):
        try:
            return self.json['tracking_id'][0]
        except KeyError:
            return None


class AggregationResult(BaseResult):
    """
    A result object for ESGF aggregations.  Properties from :class:`BaseResult` are inherited.

    :property aggregation_id: The aggregation id
    """
    @property
    def aggregation_id(self):
        return self.json['id']


_result_classes = {
    TYPE_DATASET: DatasetResult,
    TYPE_FILE: FileResult,
    TYPE_AGGREGATION: AggregationResult,
    }
