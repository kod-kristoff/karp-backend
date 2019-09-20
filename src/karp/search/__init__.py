

from karp.search._search import SearchInterface, Query  # noqa: F401
from . import errors  # noqa: F401


search = None


def init(x: SearchInterface):
    global search
    search = x
    print("Setting search = {x}".format(x=x))
