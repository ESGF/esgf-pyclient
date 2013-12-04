"""
Generate ESGF manifest files from ESGF search results

!TODO: Manifest specification

"""

import os

from pyesgf.exceptions import Error

class Manifest(object):
    VERSION = '0.1'

    def __init__(self):
        self._contents = {}

    @classmethod
    def from_result(cls, dataset_result):
        """
        Instantiate a Manifest instance from a :class:`search.results:DatasetResult`.
        
        """

        ctx = dataset_result.file_context()
        obj = cls()
        for file_result in ctx.search():
            filename = file_result.filename
            #!TODO: trap exceptions here
            filehash = '%s:%s' % (file_result.checksum_type.lower(), 
                                  file_result.checksum)
            tracking_id = file_result.tracking_id
            if tracking_id is None:
                tracking_id = ''
            size = file_result.size

            obj.add(filename, filehash, tracking_id, size)

        return obj

    @classmethod
    def from_mapfile(cls, mapfile):
        #!TODO
        pass


    def add(self, filename, filehash, tracking_id, size):
        if filename in self._contents:
            raise Error('Filename %s occurs multiple times in dataset %s' %
                        (filename, dataset_result.dataset_id))

        self._contents[filename] = (filehash, tracking_id, size)


    def write(self, fh):
        fh.write('#%esgf-manifest {0}\n'.format(self.VERSION))
        for filename in sorted(self._contents):
            filehash, tracking_id, size = self._contents[filename]
            fh.write('{0},{1},{2},{3}'.format(filename, filehash, tracking_id, size)+'\n')
