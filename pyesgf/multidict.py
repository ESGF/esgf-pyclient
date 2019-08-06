# (c) 2005 Ian Bicking and contributors; written for Paste
# (http://pythonpaste.org) Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license.php
#
# Taken verbatim from
# https://github.com/Pylons/webob/blob/master/webob/multidict.py
#
# With GetDict removed, some python 3 compatiblity added and
# flake8 clean-up.
"""
Gives a multi-value dictionary object (MultiDict) plus several wrappers
"""
from collections import MutableMapping

import binascii
import warnings


__all__ = ['MultiDict', 'NestedMultiDict', 'NoVars']


class MultiDict(MutableMapping):
    """
        An ordered dictionary that can have multiple values for each key.
        Adds the methods getall, getone, mixed and extend and add to the normal
        dictionary interface.
    """

    def __init__(self, *args, **kw):
        if len(args) > 1:
            raise TypeError("MultiDict can only be called with one positional "
                            "argument")
        if args:
            if hasattr(args[0], 'iteritems'):
                items = list(args[0].iteritems())
            elif hasattr(args[0], 'items'):
                items = list(args[0].items())
            else:
                items = list(args[0])
            self._items = items
        else:
            self._items = []
        if kw:
            self._items.extend(list(kw.items()))

    @classmethod
    def view_list(cls, lst):
        """
        Create a dict that is a view on the given list
        """
        if not isinstance(lst, list):
            raise TypeError(
                "%s.view_list(obj) takes only actual list objects, not %r"
                % (cls.__name__, lst))
        obj = cls()
        obj._items = lst
        return obj

    @classmethod
    def from_fieldstorage(cls, fs):
        """
        Create a dict from a cgi.FieldStorage instance
        """
        obj = cls()
        # fs.list can be None when there's nothing to parse
        for field in fs.list or ():
            charset = field.type_options.get('charset', 'utf8')
            transfer_encoding = field.headers.get('Content-Transfer-Encoding',
                                                  None)
            supported_transfer_encoding = {
                'base64': binascii.a2b_base64,
                'quoted-printable': binascii.a2b_qp
            }
            if charset == 'utf8':
                def decode(b):
                    return b
            else:
                def decode(b):
                    return b.encode('utf8').decode(charset)
            if field.filename:
                field.filename = decode(field.filename)
                obj.add(field.name, field)
            else:
                value = field.value
                if transfer_encoding in supported_transfer_encoding:
                    # binascii accepts bytes
                    value = value.encode('utf8')
                    value = (supported_transfer_encoding
                             [transfer_encoding](value))
                    # binascii returns bytes
                    value = value.decode('utf8')
                obj.add(field.name, decode(value))
        return obj

    def __getitem__(self, key):
        for k, v in reversed(self._items):
            if k == key:
                return v
        raise KeyError(key)

    def __setitem__(self, key, value):
        try:
            del self[key]
        except KeyError:
            pass
        self._items.append((key, value))

    def add(self, key, value):
        """
        Add the key and value, not overwriting any previous value.
        """
        self._items.append((key, value))

    def getall(self, key):
        """
        Return a list of all values matching the key (may be an empty list)
        """
        return [v for k, v in self._items if k == key]

    def getone(self, key):
        """
        Get one value matching the key, raising a KeyError if multiple
        values were found.
        """
        v = self.getall(key)
        if not v:
            raise KeyError('Key not found: %r' % key)
        if len(v) > 1:
            raise KeyError('Multiple values match %r: %r' % (key, v))
        return v[0]

    def mixed(self):
        """
        Returns a dictionary where the values are either single
        values, or a list of values when a key/value appears more than
        once in this dictionary.  This is similar to the kind of
        dictionary often used to represent the variables in a web
        request.
        """
        result = {}
        multi = {}
        for key, value in list(self.items()):
            if key in result:
                # We do this to not clobber any lists that are
                # *actual* values in this dictionary:
                if key in multi:
                    result[key].append(value)
                else:
                    result[key] = [result[key], value]
                    multi[key] = None
            else:
                result[key] = value
        return result

    def dict_of_lists(self):
        """
        Returns a dictionary where each key is associated with a list
        of values.
        """
        r = {}
        for key, val in list(self.items()):
            r.setdefault(key, []).append(val)
        return r

    def __delitem__(self, key):
        items = self._items
        found = False
        for i in range(len(items) - 1, -1, -1):
            if items[i][0] == key:
                del items[i]
                found = True
        if not found:
            raise KeyError(key)

    def __contains__(self, key):
        for k, v in self._items:
            if k == key:
                return True
        return False

    has_key = __contains__

    def clear(self):
        del self._items[:]

    def copy(self):
        return self.__class__(self)

    def setdefault(self, key, default=None):
        for k, v in self._items:
            if key == k:
                return v
        self._items.append((key, default))
        return default

    def pop(self, key, *args):
        # TODO: is this used? Differs from overridden `pop` method.
        if len(args) > 1:
            raise TypeError("pop expected at most 2 arguments, got %s"
                            % repr(1 + len(args)))
        for i in range(len(self._items)):
            if self._items[i][0] == key:
                v = self._items[i][1]
                del self._items[i]
                return v
        if args:
            return args[0]
        else:
            raise KeyError(key)

    def popitem(self):
        return self._items.pop()

    def update(self, *args, **kw):
        if args:
            lst = args[0]
            if len(lst) != len(dict(lst)):
                # this does not catch the cases where we overwrite existing
                # keys, but those would produce too many warning
                msg = ("Behavior of MultiDict.update() has changed "
                       "and overwrites duplicate keys. "
                       "Consider using .extend()")
                warnings.warn(msg, UserWarning, stacklevel=2)
        MutableMapping.update(self, *args, **kw)

    def extend(self, other=None, **kwargs):
        if other is None:
            pass
        elif hasattr(other, 'items'):
            self._items.extend(list(other.items()))
        elif hasattr(other, 'keys'):
            for k in list(other.keys()):
                self._items.append((k, other[k]))
        else:
            for k, v in other:
                self._items.append((k, v))
        if kwargs:
            self.update(kwargs)

    def __repr__(self):
        items = list(map('(%r, %r)'.__mod__, _hide_passwd(list(self.items()))))
        return '%s([%s])' % (self.__class__.__name__, ', '.join(items))

    def __len__(self):
        return len(self._items)

    #
    # All the iteration:
    #

    def iterkeys(self):
        for k, v in self._items:
            yield k

    keys = iterkeys

    __iter__ = iterkeys

    def iteritems(self):
        return iter(self._items)

    items = iteritems

    def itervalues(self):
        for k, v in self._items:
            yield v

    values = itervalues


_dummy = object()


class NestedMultiDict(MultiDict):
    """
    Wraps several MultiDict objects, treating it as one large MultiDict
    """

    def __init__(self, *dicts):
        self.dicts = dicts

    def __getitem__(self, key):
        for d in self.dicts:
            value = d.get(key, _dummy)
            if value is not _dummy:
                return value
        raise KeyError(key)

    def _readonly(self, *args, **kw):
        raise KeyError("NestedMultiDict objects are read-only")
    __setitem__ = _readonly
    add = _readonly
    __delitem__ = _readonly
    clear = _readonly
    setdefault = _readonly
    pop = _readonly
    popitem = _readonly
    update = _readonly

    def getall(self, key):
        result = []
        for d in self.dicts:
            result.extend(d.getall(key))
        return result

    # Inherited:
    # getone
    # mixed
    # dict_of_lists

    def copy(self):
        return MultiDict(self)

    def __contains__(self, key):
        for d in self.dicts:
            if key in d:
                return True
        return False

    has_key = __contains__

    def __len__(self):
        v = 0
        for d in self.dicts:
            v += len(d)
        return v

    def __bool__(self):
        for d in self.dicts:
            if d:
                return True
        return False

    def iteritems(self):
        for d in self.dicts:
            for item in list(d.items()):
                yield item

    items = iteritems

    def itervalues(self):
        for d in self.dicts:
            for value in list(d.values()):
                yield value

    values = itervalues

    def __iter__(self):
        for d in self.dicts:
            for key in d:
                yield key

    iterkeys = __iter__

    keys = iterkeys


class NoVars(object):
    """
    Represents no variables; used when no variables
    are applicable.
    This is read-only
    """

    def __init__(self, reason=None):
        self.reason = reason or 'N/A'

    def __getitem__(self, key):
        raise KeyError("No key %r: %s" % (key, self.reason))

    def __setitem__(self, *args, **kw):
        raise KeyError("Cannot add variables: %s" % self.reason)

    add = __setitem__
    setdefault = __setitem__
    update = __setitem__

    def __delitem__(self, *args, **kw):
        raise KeyError("No keys to delete: %s" % self.reason)
    clear = __delitem__
    pop = __delitem__
    popitem = __delitem__

    def get(self, key, default=None):
        return default

    def getall(self, key):
        return []

    def getone(self, key):
        return self[key]

    def mixed(self):
        return {}
    dict_of_lists = mixed

    def __contains__(self, key):
        return False
    has_key = __contains__

    def copy(self):
        return self

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__,
                             self.reason)

    def __len__(self):
        return 0

    def iterkeys(self):
        return iter([])

    keys = iterkeys
    items = iterkeys
    values = iterkeys

    __iter__ = iterkeys


def _hide_passwd(items):
    for k, v in items:
        if ('password' in k or 'passwd' in k or 'pwd' in k):
            yield k, '******'
        else:
            yield k, v
