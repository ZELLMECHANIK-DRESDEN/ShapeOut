import abc
from pathlib import PurePath

abc_ABC = abc.ABCMeta('ABC', (object,), {'__slots__': ()})


def _PurePath__fspath__(self):
    return str(self)

class os_PathLike(abc_ABC):
    """Abstract base class for implementing the file system path protocol."""

    @abc.abstractmethod
    def __fspath__(self):
        """Return the file system path representation of the object."""
        raise NotImplementedError

    @classmethod
    def __subclasshook__(cls, subclass):
        if PurePath is not None and issubclass(subclass, PurePath):
            return True
        return hasattr(subclass, '__fspath__')


def safe_path(path):
    """Return the path representation of a path-like object ASCII-safe.
    ASCII-safe means that all non-ASCII characters are replaced with "X".
    If str or bytes is passed in, it is returned unchanged. Otherwise the
    os.PathLike interface is used to get the path representation. If the
    path representation is not str or bytes, TypeError is raised. If the
    provided path is not str, bytes, or os.PathLike, TypeError is raised.
    """
    if isinstance(path, (str, bytes)):
        return safe_str(path)

    # Work from the object's type to match method resolution of other magic
    # methods.
    path_type = type(path)
    try:
        path_repr = path_type.__fspath__(path)
    except AttributeError:
        if hasattr(path_type, '__fspath__'):
            raise
        elif PurePath is not None and issubclass(path_type, PurePath):
            return safe_str(_PurePath__fspath__(path))
        else:
            raise TypeError("expected str, bytes or os.PathLike object, "
                            "not " + path_type.__name__)
    if isinstance(path_repr, (str, bytes)):
        return safe_str(path_repr)
    else:
        raise TypeError("expected {}.__fspath__() to return str or bytes, "
                        "not {}".format(path_type.__name__,
                                        type(path_repr).__name__))


def safe_str(astr):
    dec = str(astr).decode("ascii", "replace")
    return dec.replace(u"\ufffd", "X").replace(u"?", "X")


def path_to_str(path):
    """This is a heuristic function"""
    try:
        string = str(path)
    except UnicodeDecodeError:
        try:
            string = unicode(path)  # noqa: F821
        except BaseException:
            try:
                string = unicode(path).encode("utf-8")  # noqa: F821
            except BaseException:
                string = str(path).decode("utf-8")
    return string
