"""
Search results are retrieved through the ResultSet class.  This class
hides paging of large result sets behind a client-side cache.

"""

from collections import Sequence

from .consts import DEFAULT_BATCH_SIZE

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
            self.__get_batch(0)

    def __getitem__(self, index):
        batch_i = index / self.batch_size
        offset = index % self.batch_size
        if self.__batch_cache[batch_i] is None:
            batch = self.__batch_cache[batch_i] = self.__get_batch(batch_i)
            
        return batch[offset]
            

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
        response = self.context.connection.send_query(query_dict, limit=limit, offset=offset)

        #!TODO: strip out results
        return response['response']['docs']
