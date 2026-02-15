import psycopg


class DatabaseConnection:
    """
    Database connection using the singleton pattern. creating an new instance after creation of the DatabaseConncetion
    gives the singleton object.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            print("Creating new database connection")
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, conn_string):
        # Only initialize once
        if not self._initialized:
            print("Initializing database connection")
            self.connection_string = conn_string
            self.connection = psycopg.connect(conn_string)
            self._initialized = True

    def get_connection(self):
        return self.connection
