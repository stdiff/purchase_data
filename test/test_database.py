"""
test for database.py
"""

from unittest import TestCase
from datetime import datetime

import numpy as np
import pandas as pd

from lib.database import Database

class TestDatabase(TestCase):
    def test_database(self):

        with Database(sql_path="test/test_ddl.sql") as db:
            db.initialize_db()

            ## check the number of tables
            sql = "SELECT name FROM sqlite_master WHERE type = 'table'"
            df_tables = db.read_query(sql)
            self.assertTrue(isinstance(df_tables, pd.DataFrame))
            self.assertEqual(list(df_tables.name), ["Test"])

            ## inserts data
            df_data = pd.DataFrame({"itemID": range(11)})
            df_data["insert_ts"] = datetime.now().isoformat(sep=" ")[:len("yyyy-mm-dd HH:MM:SS")]
            df_data["random"] = np.random.uniform(0,10,size=11)
            db.insert_data(df_data, "Test", if_exists="append", index=False)

            ## check inserted data
            df = db.read_table("Test")
            self.assertTrue(isinstance(df,pd.DataFrame))
            self.assertEqual(df.shape, (11,3))
            self.assertEqual(df.dtypes[0], "int64")
            self.assertEqual(df.dtypes[1], "object")
            self.assertEqual(df.dtypes[2], "float64")

