"""
Generate ESGF manifest files from ESGF search results

!TODO: Manifest specification

"""

import os
import urllib2
import csv

from pyesgf.exceptions import Error

import logging
log = logging.getLogger(__name__)

class Manifest(object):
    VERSION = '0.1'

    def __init__(self, drs_id):
        self.drs_id = drs_id
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
        raise NotImplementedError


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



class ManifestExtractor(object):
    SOLR_BATCH_SIZE = 500


class SolrManifestExtractor(ManifestExtractor):
    SOLR_FIELDS = ['dataset_id', 'title', 'checksum_type', 'checksum',
                   'tracking_id','size']

    def __init__(self, endpoint, project):
        self.endpoint = endpoint
        self.project = project

    def _query(self, offset):
        params = (
            ('q', '*'),
            ('fq', 'project:{0}'.format(self.project)),
            ('fl', ','.join(self.SOLR_FIELDS)),
            ('wt', 'csv'),
            ('sort', 'dataset_id%20asc'),
            ('start', offset),
            ('rows', self.SOLR_BATCH_SIZE),
            )
        param_str = '&'.join(('{0}={1}'.format(k, v)) for (k, v) in params)

        url = '{0}/solr/files/select?{1}'.format(self.endpoint,
                                                 param_str)
        log.info('SOLR QUERY: {0}'.format(url))
        response = urllib2.urlopen(url)
        
        return response

    def _check_header(self, header):
        if header != self.SOLR_FIELDS:
            raise Error('Unrecognised SOLr CSV header')


    def _init_manifest(self, dataset_id):
        drs_id, datanode = dataset_id.split('|')
        log.info('Generating manifest {0}'.format(drs_id))

        return Manifest(drs_id)


    def iter(self):
        """
        Query the SOLr index until all files for this project have been extracted.
 
        """

        offset = 0
        current_dataset_id = None
        current_manifest = None
        while 1:
            response = self._query(offset)
            reader = csv.reader(response)

            # Read first line and check the header
            header = reader.next()
            self._check_header(header)

            empty_batch = True
            for row in reader:
                empty_batch = False

                log.debug('ROW: {0}'.format(row))
                dataset_id, filename, checksum_type, checksum, tracking_id, size = row
                if dataset_id != current_dataset_id:
                    if current_manifest:
                        yield current_manifest
                    current_manifest = self._init_manifest(dataset_id)                    
                    current_dataset_id = dataset_id

                filehash = '{0}:{1}'.format(checksum_type.lower(), checksum)
                size = int(size)

                current_manifest.add(filename, filehash, tracking_id, size)

            # Test whether there were any rows.  If not we have reached the end.
            if empty_batch:
                break
            else:
                offset += self.SOLR_BATCH_SIZE

        if current_manifest:
            yield current_manifest
