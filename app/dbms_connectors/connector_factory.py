from app.dbms_connectors.implements.sqlite_connector import SqliteConnector


def get_connector_by_dbms_name(db_name: str, **db_config):
    if db_name == "sqlite":
        return SqliteConnector(**db_config)
    else:
        return None