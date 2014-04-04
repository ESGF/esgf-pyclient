"""
Generate ESGF manifest files from ESGF search results

!TODO: Manifest specification

"""

import os
import urllib2
import csv
import re
import datetime

from pyesgf.exceptions import Error, DuplicateHashError

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
            old_filehash, old_tracking_id, old_size = self._contents[filename]
            if old_filehash == filehash:
                log.warn('Filename {0} occurs multiple times in dataset {1} '
                         'with the same hash'.format(filename, self.drs_id))
            elif old_tracking_id == tracking_id:
                raise DuplicateHashError(
                    'Filename {0} occurs multiple times in dataset {1} with '
                    'the same tracking_id and different hash'.format(filename,
                                                                     self.drs_id))
            else:
                raise DuplicateHashError(
                    'Filename {0} occurs multiple times in '
                    'dataset {1}'.format(filename, self.drs_id))
            
        self._contents[filename] = (filehash, tracking_id, size)


    def write(self, fh):
        fh.write('#%esgf-manifest {0}\n'.format(self.VERSION))
        for filename in sorted(self._contents):
            filehash, tracking_id, size = self._contents[filename]
            fh.write('{0},{1},{2},{3}'.format(filename, filehash, tracking_id, size)+'\n')



class ManifestExtractor(object):
    pass


class SolrManifestExtractor(ManifestExtractor):
    SOLR_BATCH_SIZE = 1000
    SOLR_FIELDS = ['dataset_id', 'title', 'checksum_type', 'checksum',
                   'tracking_id','size']

    def __init__(self, endpoint, project, from_date=None):
        self.endpoint = endpoint
        self.project = project
        self.from_date = from_date

    def _query(self, offset):
        fq = 'project:{0}'.format(self.project)
        if self.from_date:
            fq += ' AND timestamp[{0}Z TO NOW]'.format(self.from_date)

        params = (
            ('q', '*'),
            ('fq', fq),
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


    def __iter__(self):
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

                try:
                    current_manifest.add(filename, filehash, tracking_id, size)
                except DuplicateHashError, e:
                    log.error(e)

            # Test whether there were any rows.  If not we have reached the end.
            if empty_batch:
                break
            else:
                offset += self.SOLR_BATCH_SIZE

        if current_manifest:
            yield current_manifest


def cmip5_manifest_partitioner(drs_id):
    """
    Split a drs_id into pragmatic components for constructing a directory structure.
    This partition is designed to balance the need to split a repository between
    subdirectories with the desire to minimise the depth of the tree.

    """
    (activity, product, institute, model, experiment, 
     frequency, realm, table, ensemble, version) = drs_id.split('.')

    parts = ('.'.join((activity, product, institute)),
             '.'.join((model, experiment, frequency)))
    
    return parts



def extract_from_solr(endpoint, project, target_dir, from_date=None):
    solr_extractor = SolrManifestExtractor(endpoint, project, from_date)

    for manifest in solr_extractor:

        manifest_path = os.path.join(target_dir,
                                     *cmip5_manifest_partitioner(manifest.drs_id))
        if not os.path.exists(manifest_path):
            log.info('Creating repo directory {0}'.format(manifest_path))
            os.makedirs(manifest_path)
        
        manifest_file = os.path.join(manifest_path, manifest.drs_id)


        if os.path.exists(manifest_file):
            log.warn('Manifest {0} already exists.  This manifest will be overwritten'.format(manifest_file))

        with open(manifest_file, 'w') as fh:
            log.info('Writing Manifest {0}'.format(manifest_file))
            manifest.write(fh)


def parse_timestamp(timestamp):
    """
    Parses a standard ISO timestamp.  This function allows the time to be ommitted but
    if present it must include hours, minutes and seconds.

    """
    if re.match(r'\d{4}-\d{2}-\d{2}$', timestamp):
        timestamp += 'T00:00:00Z'
    elif timestamp[-1] != 'Z':
        timestamp += 'Z'

    dt = datetime.datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')

    return dt

if __name__ == '__main__':
    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description='Extract ESGF datasets from a SOLr index into a manifest repository')
    parser.add_argument('endpoint', help='SOLr endpoint as http://<host>:<port>')
    parser.add_argument('project', help='The project to extract')
    parser.add_argument('repository', help='Path to the manifest repository')
    parser.add_argument('--from', dest='from_date', action='store', 
                        help='The minimum timestamp of returned SOLr records')

    args = parser.parse_args()

    if args.from_date:
        from_date = parse_timestamp(args.from_date)
    else:
        from_date is None

    extract_from_solr(args.endpoint, args.project, args.repository, from_date=from_date)
