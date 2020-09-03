import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from karp import config


engine = sqlalchemy.create_engine(config.DB_URL)

print(f"Engine created to '{config.DB_URL}'")


@sqlalchemy.event.listens_for(engine, "do_connect")
def receive_do_connect(dialect, conn_rec, cargs, cparams):
    print(f"dialect = {dialect}, {str(dialect)}")
    if str(dialect).startswith("<sqlalchemy.dialects.sqlite"):
        print(f"Sqlite database detected.")
        cparams["check_same_thread"] = False


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# from typing import Optional

#


# class SQLAlchemy(_BaseSQLAlchemy):

#     def apply_pool_defaults(self, app, options):
#         super(SQLAlchemy, self).apply_pool_defaults(app, options)
#         # options['echo'] = True
