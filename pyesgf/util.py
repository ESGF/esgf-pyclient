"""
Utility functions using the pyesgf package.

"""

import sys
from urllib import quote_plus, _is_unicode

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
            

def urlencode(query):
    """Encode a sequence of two-element tuples or dictionary into a URL query string.

    This version is adapted from the standard library to understand operators in the
    pyesgf.search.constraints module.

    If the query arg is a sequence of two-element tuples, the order of the
    parameters in the output will match the order of parameters in the
    input.
    """

    if hasattr(query,"items"):
        # mapping objects
        query = query.items()
    else:
        # it's a bother at times that strings and string-like objects are
        # sequences...
        try:
            # non-sequence items should not work with len()
            # non-empty strings will fail this
            if len(query) and not isinstance(query[0], tuple):
                raise TypeError
            # zero-length sequences of all types will get here and succeed,
            # but that's a minor nit - since the original implementation
            # allowed empty dicts that type of behavior probably should be
            # preserved for consistency
        except TypeError:
            ty,va,tb = sys.exc_info()
            raise TypeError, "not a valid non-string sequence or mapping object", tb


    def append(k, v, tag, l):
        from .search.consts import OPERATOR_NEQ

        if tag == OPERATOR_NEQ:
            l.append('%s!=%s' % (k, v))
        elif tag is None:
            l.append('%s=%s' % (k, v))
        else:
            raise ValueError('Unknown operator tag %s' % tag)

    def strip_tag(v):
        if type(v) == tuple:
            tag, v = v
        else:
            tag = None
            
        return tag, v

    l = []
    for k, v in query:
        tag, v = strip_tag(v)
        k = quote_plus(str(k))
        if isinstance(v, str):
            v = quote_plus(v)
            append(k, v, tag, l)
        elif _is_unicode(v):
            # is there a reasonable way to convert to ASCII?
            # encode generates a string, but "replace" or "ignore"
            # lose information and "strict" can raise UnicodeError
            v = quote_plus(v.encode("ASCII","replace"))
            append(k, v, tag, l)
        else:
            try:
                # is this a sufficient test for sequence-ness?
                len(v)
            except TypeError:
                # not a sequence
                v = quote_plus(str(v))
                append(k, v, tag, l)
            else:
                # loop over the sequence
                for elt in v:
                    append(k, quote_plus(str(elt)), tag, l)
    return '&'.join(l)
