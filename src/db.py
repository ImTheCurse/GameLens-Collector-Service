from psycopg_pool import ConnectionPool


class DatabaseConnection:
    """
    A Singleton wrapper around a Connection Pool.
    """

    _pool = None

    @classmethod
    def initialize(cls, conn_string):
        if cls._pool is None:
            print("Initializing Connection Pool...")
            cls._pool = ConnectionPool(conn_string, min_size=1, max_size=10)

    @classmethod
    def get_connection(cls):
        """
        Returns a context manager that yields a connection from the pool.
        """
        if cls._pool is None:
            raise Exception(
                "Database not initialized. Call Database.initialize() first."
            )

        # Usage: with Database.get_connection() as conn: ...
        return cls._pool.connection()

    @classmethod
    def close(cls):
        """
        Clean up the pool on app shutdown.
        """
        if cls._pool:
            cls._pool.close()
            print("Connection Pool closed.")
