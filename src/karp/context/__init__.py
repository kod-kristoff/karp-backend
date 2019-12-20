"""Handle all low-level queries."""
from .context import SQL
from .context import SQLwES6


ctx = None


def init(app):
    """Initialize the context.

    Arguments:
        app {Flask} -- The app to create the context for.

    Raises:
        RuntimeError: If something goes wrong.
    """
    global ctx
    if app.config["ELASTICSEARCH_ENABLED"]:
        if not app.config.get("ELASTICSEARCH_HOST"):
            raise RuntimeError("No host for ES")
        ctx = SQLwES6(app)
    else:
        ctx = SQL(app)

