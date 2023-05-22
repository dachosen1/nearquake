from psycopg2 import connect, sql

class DbOperator:
    """
    Connects to and executes database SQL queries
    """

    def __init__(self):
        self.connection = None
        self.cursor = None

    def connect(self, host, user, password, dbname, port):
        """
        :param host: Host name
        :param user: User name
        :param password: Password
        :param dbname: Database name
        """

        self.host = host
        self.dbname = dbname
        self.port = port

        try:
            self.connection = connect(
                host=host, user=user, password=password, dbname=dbname, port=port
            )
            self.cursor = self.connection.cursor()
        except Exception as e:
            _logger.error(f"Failed to connect to the database: {e}")

    def fetch(self, query, type="all"):
        """
        Executes an SQL query

        :param query: SQL Query
        :param mode: Specifies the type of query. Options are 'all' (retrieves all rows) and 'one' (returns a single row).
        Defaults to 'all'.
        """
        try:
            self.cursor.execute(sql.SQL(query))
            if type == "all":
                return self.cursor.fetchall()
            elif type == "one":
                return self.cursor.fetchone()
            else:
                raise ValueError("Invalid type. Expected 'all' or 'one'.")

        except Exception as e:
            print("Failed to execute fetch query: ", e)

    def insert(self, query, data, mode):
        """
        Insert data into the database.

        :param query: SQL Query
        :param data: Data
        :param mode: _description_
        """
        try:
            if mode == "one":
                return self.cursor.execute(sql.SQL(query), data)

            elif mode == "all":
                return self.cursor.executemany(sql.SQL(query), data)

        except Exception as e:
            print("Failed to execute insert query: ", e)

    def close(self):
        self.cursor.close()
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class QueryExecutor:
    """
    Functions to run SQL queries and exit the connection to the database
    """

    def __init__(self, database):
        self.database = database

    def fetch(self, query, mode):
        """
        Fetch data from a database and close the database connection.

        :param query: SQL Query
        :param mode: Specifies the type of query. Options are 'all' (retrieves all rows) and 'one' (returns a single row).
        Defaults to 'all'.
        """
        with self.database as db:
            return db.fetch(query, mode)

    def insert(self, query, data, mode):
        """
        Insert data into a database and close the database connection.

        :param query: SQL Query
        :param mode: Specifies the type of query. Options are 'all' (retrieves all rows) and 'one' (returns a single row).
        Defaults to 'all'.
        """
        with self.database as db:
            return db.insert(query, data, mode)