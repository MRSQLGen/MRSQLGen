import sqlite3
from datetime import datetime, date
import gc
import time
from app.dbms_connectors.interfaces.dbms_connector import DbmsConnector


class SqliteConnector(DbmsConnector):
    """
    SqliteConnector  DbmsConnector ， SQLite 。
     SQL 、、。

    SqliteConnector is an implementation of DbmsConnector,
    providing support for interacting with SQLite databases,
    including execution, streaming, and data formatting.
    """
    def __init__(self, **db_config):
        """
        ， SQLite ，。

        Initialize the connector:
        - Extracts SQLite DB path from config
        - Establishes a connection
        """
        self.db_path = db_config['db_path']
        self.conn = None
        super(SqliteConnector, self).__init__(**db_config)
        self._create_connection() #  / Establish DB connection

    def _create_connection(self):
        """
         sqlite3 。

        Create SQLite database connection.
        """
        self.conn = sqlite3.connect(self.db_path)

    def execute(self, sql):
        """
         SQL ，、。

        Execute any SQL statement (SELECT, INSERT, UPDATE, DELETE, etc.).
        Returns:
            - query result (list of rows or empty list),
            - affected row count,
            - error message (empty string if no error).

        ：
        -  INSERT()、UPDATE()、DELETE ，rowcount 。
        -  SELECT ， SQLite  rowcount  -1（ SQLite ，）。
        """
        result = None
        rowcount = -1
        err = ""
        cursor = self.conn.cursor()
        try:
            cursor.execute(sql)
            if sql.strip().upper().startswith("SELECT"):
                result = cursor.fetchall()  #  / Fetch result rows
            else:
                result = None
                self.conn.commit()  #  / Commit changes
            rowcount = cursor.rowcount #  / Get row count

            # # ，：
            # rowcount = len(result)
        except Exception as e:
            err = str(e)
            print(f"[SQL Exec Error] {e}\nError SQL: {sql}")
        finally:
            cursor.close()  #  cursor / Always close the cursor
        return result if result is not None else [], rowcount, err

    def create_database(self, database_name):
        """
        SQLite ，。

        Database creation in SQLite is handled via file creation externally.
        """
        pass

    def drop_database(self, database_name):
        """
        SQLite 。

        Dropping a SQLite DB means deleting the database file externally.
        """
        pass

    def close(self):
        """
        （）。

        Close the SQLite database connection (if open).
        """
        if self.conn:
            self.conn.close()
            self.conn = None
            # ，
            gc.collect()
            time.sleep(0.1)  #  100ms

    def stream_query(self, query_sql, batch_size: int = 100):
        """
        ：，。

        Stream query results in batches (e.g., 100 rows at a time).
        Useful for large datasets to reduce memory usage.

        Args:
            query_sql (str):  SELECT SQL
            batch_size (int):
        Yields:
            row:
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute(query_sql)
            while True:
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break
                for row in rows:
                    yield row
        finally:
            cursor.close()

    def stream_query_record_count(self, table_name):
        """
        。

        Count total number of records in a table.
        """
        sql_statement = f"SELECT COUNT(*) FROM {table_name};"
        result, _,_ = self.execute(sql_statement)
        return result[0][0]

    def stream_query_columns(self, table_name, column_names):
        """
        。

        Stream selected columns from a table.

        Args:
            table_name (str):  / Table name
            column_names (list):  / List of column names
        """
        sql_statement = f"SELECT {', '.join(column_names)} FROM {table_name};"
        yield from self.stream_query(sql_statement)

    def record_to_str(self, record):
        """
        】。

        Format a database record (tuple) into a string for SQL usage.
        Handles various data types (NULL, str, datetime, bytes, etc.)

        Args:
            record (tuple):  / One row of data
        Returns:
            str:  / Formatted value string
        """
        results = list()
        for value in record:
            if value is None:
                results.append("NULL")
            elif isinstance(value, str):
                # datetime
                try:
                    if "." in value:
                        dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")  # sqlite
                    else:
                        dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                    results.append(f"""'{dt.strftime("%Y-%m-%d %H:%M:%S")}'""")
                except Exception:
                    # results.append(f"'{value}'")
                    value = value.replace("\\n", "\n").replace("\\r", "\r").replace("\\t", "\t").replace("\\b", "\b")
                    results.append(f"'{value}'")
            elif isinstance(value, datetime):
                results.append(f"""'{value.strftime("%Y-%m-%d %H:%M:%S")}'""")
            elif isinstance(value, date):
                results.append(f"""'{value.strftime("%Y-%m-%d")}'""")
            elif isinstance(value, int):
                results.append(str(value))
            elif isinstance(value, float):
                results.append("{:.6f}".format(value))
            elif isinstance(value, memoryview):
                value = bytes(value)
                results.append(f"'0x{value.hex().upper()}'")
            elif isinstance(value, bytes):
                results.append(f"'0x{value.hex().upper()}'")
            else:
                results.append(str(value))
        return f"({', '.join(results)})"