from distutils.util import strtobool
import os

from .context import SQLwES6


def _create_context():
    if strtobool(os.environ.get("ELASTICSEARCH_ENABLED")):
        return SQLwES6()
    else:
        raise RuntimeError("No context loaded.")


ctx = _create_context()
# del _create_context


def set_context(context_name: str = None):
    global ctx
    if not context_name:
        ctx = SQLwES6()
