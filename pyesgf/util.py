"""
Utility functions using the pyesgf package.

"""

def get_manifest(drs_id, version, connection):
    """
    Retrieve the filenames, sizes and checksums of a dataset.

    This function will raise ValueError if more than one dataset is found
    matching the given drs_id and version on a search without replicas.
    The connection should be either distrib=True or be connected to a suitable
    ESGF search interface.

    :param drs_id: a string containing the DRS identifier without version
    :param version: The version as a string or int

    """

    if type(version) == int:
        version = str(version)

    context = connection.new_context(drs_id=drs_id, version=version)
    results = context.search()

    if len(results) > 1:
        raise ValueError("Search for dataset %s.v%s returns multiple hits" % 
                         (drs_id, version))

    file_context = results[0].file_context()
    manifest = {}
    for file in file_context.search():
        manifest[file.filename] = {
                'checksum_type': file.checksum_type,
                'checksum': file.checksum,
                'size': file.size,
                }

    return manifest
            
