from psycopg2 import connect, sql


class DatabaseOperator:
    """
      Connects to and executes database SQL queries
    """
    def __init__(self, host, user, password, dbname):
        """
        :param host: Host name 
        :param user: User name
        :param password: Password
        :param dbname: Database name 
        """
        self.connection = connect(
            host=host,
            user=user,
            password=password,
            dbname=dbname,
        )
        self.cursor = self.connection.cursor()

    def execute(self, query, mode='all'):
        """
        Executes an SQL query

        :param query: SQL Query 
        :param mode: Specifies the type of query. Options are 'all' (retrieves all rows) and 'one' (returns a single row).
        Defaults to 'all'.
        """

        self.cursor.execute(sql.SQL(query))
        if mode=='all':
            return self.cursor.fetchall()
        elif mode == 'one':
            return self.cursor.fetchone()
        else:
            raise ValueError("Invalid type. Expected 'all' or 'one'.")


    def close(self):
        self.cursor.close()
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self):
        self.close_connection()


class QueryExecutor:
    """
      Functions to run SQL queries
    """
    def __init__(self, database):
        self.database = database

    def run_query(self, query, mode):
        """_summary_

        :param query: SQL Query 
        :param mode: Specifies the type of query. Options are 'all' (retrieves all rows) and 'one' (returns a single row).
        Defaults to 'all'.
        """
        with self.database as db:
            return db.execute(query, mode)