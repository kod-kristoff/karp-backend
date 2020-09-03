from karp.database import SessionLocal
from karp import models

# from karp import create_app
# from karp.application.config import MariaDBConfig

# app = create_app(MariaDBConfig(setup_database=False))

# with SessionLocal() as db:
#     try:
#         entry_tables = [
#             resource.resource_id + "_" + str(resource.version)
#             for resource in ResourceDefinition.query.all()
#         ]
#         history_tables = [table_name + "_history" for table_name in entry_tables]
#     except Exception:
#         entry_tables = []
#         history_tables = []
def find_tables():
    db = SessionLocal()
    history_tables = []
    runtime_tables = []
    try:
        for resource in db.query(models.Resource).all():
            history_tables.append(f"{resource.resource_id}_history")
            runtime_tables.append(f"{resource.resource_id}_{resource.version}_runtime")
        return history_tables, runtime_tables
    except Exception:
        return [], []


history_tables, runtime_tables = find_tables()
