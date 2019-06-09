"""
Helper class to deal with the SQLite3 database
"""

import sqlite3
from typing import Union
from pathlib import Path

import pandas as pd

class Database:
    def __init__(self, db_path:Union[Path,str]=None, sql_path:Union[Path,str]=None):
        self.db_path: Union[str,Path] = ":memory:" if db_path is None else Path(db_path)
        self.sql_path = None if sql_path is None else Path(sql_path)

        self.connection = sqlite3.connect(str(self.db_path))
        self.cursor = self.connection.cursor()


    def initialize_db(self):
        """
        Prepare the database file and tables
        """
        if self.sql_path is None:
            raise ValueError("sql_path is not given at the instantiation")

        with self.sql_path.open("r") as ddl_file:
            sql_statement = "\n".join(ddl_file.readlines())

        try:
            self.cursor.executescript(sql_statement)
        except Exception as e:
            print("-- following sql statement is not executed")
            self.connection.rollback()
            raise Exception(e)


    def insert_data(self, data:pd.DataFrame, table:str, if_exists:str="append",
                    index:bool=False, **kwargs):
        """
        insert the given DataFrame into the tabel in DB

        :param data: DataFrame to insert
        :param table: name of the table
        :param if_exists: "append" (default), "fail" or "replace" same as if_exists in DataFrame.to_sql
        :param index: same as index in DataFrame.to_sql
        :param kwargs: passed to DataFrame.to_sql
        """
        data.to_sql(table, self.connection, if_exists=if_exists, index=index, **kwargs)


    def read_query(self, query:str, **kwargs):
        """
        execute the given query and return the result as a DataFrame

        :param query: sql query to execute
        :param kwargs: passed to pandas.read_sql
        :return: DataFrame
        """
        return pd.read_sql(query, self.connection, **kwargs)


    def read_table(self, table:str, **kwargs) -> pd.DataFrame:
        """
        read the whole table from the DB and return it as a DataFrame

        :param table: name of the table
        :param kwargs: passed to pandas.read_sql
        :return: DataFrame
        """
        sql = "SELECT * FROM %s" % table
        return self.read_query(sql, **kwargs)


    def __enter__(self):
        return self


    def close(self):
        self.connection.close()


    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
