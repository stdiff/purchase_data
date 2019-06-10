"""
This script reads the relevant CSV files and store them in an SQLite3 database.

# FAQ

Q: Why do we need to create tables in advance? Pandas creates tables automatically
   so that we do not need to care about the schema.
A: We want to keep the information about primary keys and foreign keys. We use
   such an information to create a diagram of the relation among the tables.
"""

import pandas as pd
from pathlib import Path

from lib.database import Database

data_dir = Path("data") ## directory for CSV files
sql_dir = Path("sql") ## directory for SQL files (script, database)
db_path = sql_dir.joinpath("database.sqlite") ##
sql_path = sql_dir.joinpath("data-model.sql") ## DDL script

if __name__ == "__main__":
    with Database(db_path=db_path, sql_path=sql_path) as db:
        db.initialize_db()

        tables = ["Campaigns", "Customers", "Orderlines", "Orders", "Products"]
        for table in tables:
            print("------ %s" % table)
            csv_path = data_dir.joinpath("%s.txt" % table.lower())
            df = pd.read_csv(csv_path, sep="\t", parse_dates=True, encoding="latin_1")
            db.insert_data(df,table,if_exists="append")
