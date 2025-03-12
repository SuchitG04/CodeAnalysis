import libsql_experimental as libsql

# NOTE: make sure you set the appropriate environment variables

# https://github.com/tursodatabase/libsql-experimental-python/issues/50
class ConnectionWrapper:
    def __init__(self, db_conn: libsql.Connection):
        self.db_conn = db_conn
        self.auth_token = os.getenv('TURSO_AUTH_TOKEN')
        self.retry_connection_fn = lambda: libsql.connect(os.getenv('TURSO_DB_URL'), auth_token=self.auth_token)
    
    def execute(self, *args, **kwargs):
        try:
            return self.db_conn.execute(*args, **kwargs)
        except ValueError as e:
            if "expired" in str(e) or "baton" in str(e):
                self.db_conn = self.retry_connection_fn()
                return self.db_conn.execute(*args, **kwargs)
            else:
                raise e

    def executemany(self, *args, **kwargs):
        try:
            return self.db_conn.executemany(*args, **kwargs)
        except ValueError as e:
            if "expired" in str(e) or "baton" in str(e):
                self.db_conn = self.retry_connection_fn()
                return self.db_conn.executemany(*args, **kwargs)
            else:
                raise e

    def rollback(self):
        self.db_conn.rollback()
    def commit(self):
        self.db_conn.commit()

conn = ConnectionWrapper(
    libsql.connect(os.getenv('TURSO_DB_URL'), auth_token=os.getenv('TURSO_AUTH_TOKEN'))
)
