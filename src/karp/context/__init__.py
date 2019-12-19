from .context import SQL
from .context import SQLwES6


ctx = None


def init(app):
    global ctx
    if app.config['ELASTICSEARCH_ENABLED']:
        if not app.config.get('ELASTICSEARCH_HOST'):
            raise RuntimeError('No host for ES')
        ctx = SQLwES6(app)
    else:
        ctx = SQL(app)

