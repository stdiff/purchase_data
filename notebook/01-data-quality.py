# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.3'
#       jupytext_version: 0.8.6
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# # Purchase data analysis 1: Data
#
# The aim of this notebook is to check the quality of data. 

# ![](../sql/data-model.png)

# +
from typing import *

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# +
from IPython.display import display, HTML
plt.style.use("fivethirtyeight")

from pylab import rcParams
rcParams['figure.figsize'] = 14, 6

#pd.set_option('display.max_rows', None)
# -

import sys
sys.path.append("..")
from lib.database import Database
from lib.processing import Inspector

# ## Orders
#
# This table describes all orders. Each row corresponds to one purchase. 

with Database("../sql/database.sqlite") as db:
    df_orders = db.read_table("Orders", is_datetime=lambda c: c.lower().endswith("date"))
    df_zip = db.read_table("ZipCounty")

df_orders.head()

df_orders.shape ## (number of rows, number of columns)

inspector = Inspector(df_orders)
inspector.set_variable_type("customerId","categorical")
inspector.set_variable_type("campaignId","categorical")
inspector

# The number of unique values of `orderDate` is relatively small. This is because the column represents really dates rather than time stamps.

df_orders["orderDate"].apply(lambda x: x.time()).unique() ## unique values of HH:MM:SS 

# Regarding relation among missing values in `city`, `state` and `zipCode`. There is no obvious relation between missing values of these variables: It is not the case that a missing value of one of them implies any missing value of other columns.

geo_cols = ["city","state","zipCode"]
pd.isna(df_orders[geo_cols]).groupby(geo_cols).apply(lambda x:pd.Series(x.shape[0], index=["count"]))

# But the real problem of these columns is that we can not trust their values. For example, the 100 example values of `zipCode` with a non-digit letter are following.

import re
pd.Series([v for v in df_orders["zipCode"] if not re.search(r"^\d{1,}$",str(v))]).unique()[:100]

# Moreover we can find values which are likely to be country names.

pd.Series([v for v in df_orders["zipCode"] if re.search(r"^[a-zA-Z]{1,}$",str(v))]).unique()

# A similar problem occurs also for `state`. This column contains values which are not in US.

df_orders["state"].unique()

# There are (at least) two possible measures.
#
# 1. We do not use these columns, because we can not trust them.
# 2. We restrict the data set, so that the triad (city, state, zipCode) can be found in the dataset ZipCounty. (Here we trust data set ZipCountry.)
#
# The former is easiest but we lose geographic information. The latter can be reasonable, but many data will be lost. In fact around 1/3 of the data will be lost.

# +
df_geo = df_zip[["poname","state","zipcode"]].drop_duplicates()\
                                             .rename({"poname":"city","zipcode":"zipCode"},axis=1)
df_geo["zipCode"] = df_geo["zipCode"].apply(str)
df_orders_valid = pd.merge(df_orders, df_geo, how="inner")

np.round(100*(1-df_orders_valid.shape[0]/df_orders.shape[0]),2) ## % of rows without geo info in ZipCounty
# -

# ## Customers
#
# This table describes all customers. Each row corresponds to a single customer.

# +
with Database("../sql/database.sqlite") as db:
    df_customers = db.read_table("Customers")
    
df_customers.tail()
# -

inspector_customers = Inspector(df_customers)
inspector_customers

# The most interesting variable is `householdId`. It is usually difficult to detect who belongs to the same household. But we have to note that a household can be a company or a quite large group.

df_customers["householdId"].value_counts().sort_values(ascending=False)[:10]

# ## Orderlines
#
# This table describes items of all purchases. Roughly speaking, each row corresponds a pair (`orderId`, `productId`), but this is not rigorous.

# +
with Database("../sql/database.sqlite") as db:
    df_orderlines = db.read_table("Orderlines")
    
df_orderlines.tail()
# -

# All columns have no missing values except `unitPrice`. 

inspector_orderlines = Inspector(df_orderlines)
inspector_orderlines

# The following table shows the count of rows of each pair of (`orderId`, `productId`). As you see that the pair is not a primary key.

# +
def count_rows_by(df:pd.DataFrame, by=List[str]) -> pd.DataFrame:
    """
    SELECT by[0], ..., count(*) FROM DF GROUP BY by[0], ...
    
    :return: DataFrame[by[0],...,count]
    """
    df_count = df.groupby(by).apply(lambda dg: dg.shape[0]).rename("count")\
                 .reset_index()\
                 .sort_values(by="count", ascending=False)
    return df_count

pks = ["orderId","productId"]
df_count_pairs = count_rows_by(df_orderlines, pks)
df_count_pairs.iloc[:10,:]
# -

# But theoretically we have to be able to merge these multiple rows. Lets see some examples.

# +
idx = 4
orderId, productId, _ = df_count_pairs.iloc[idx,:]

df_orderlines.query("orderId == @orderId and productId == @productId")

# +
idx = 10
orderId, productId, _ = df_count_pairs.iloc[idx,:]

df_orderlines.query("orderId == @orderId and productId == @productId").sort_values(by="shipDate")
# -

# Sometimes we have lots of duplicates and sometimes `shipDate` and `billDate` are different.

# Next let us look at the missing values of `unitPrice`.

df_orderlines[pd.isna(df_orderlines["unitPrice"])].head(20)

# As we see, something wrong happened. Probably the shipping or billing failed, so that the customer received the product quite later. Moreover we can guess that the missing value of `unitPrice` occurs if and only if the `numUnits` is zero. This guess is right.

## list of values of `numUnits` where `unitPrice` is missing.
df_orderlines["numUnits"][pd.isna(df_orderlines["unitPrice"])].unique()

## list of values of `unitPrice` where `numUnits` is zero.
df_orderlines["unitPrice"][df_orderlines["numUnits"]==0].unique()

# Therefore we can safely remove rows without `unitPrice` unless we want to see something strange.

df_orderlines.dropna(how="any", inplace=True)
# According to the above analysis we can say that the table `Orderlines` describes each *shipping* per product. Here "shipping" does not mean `shipDate`. Moreover we have to keep in mind that the `unitPrice` of the same product can vary.

count_rows_by(df_orderlines[["productId","unitPrice"]].drop_duplicates(), by=["productId"]).head()

df_orderlines.query("productId == '13629'")["unitPrice"].value_counts().head(10)

# ## Products
#
#

# +
with Database("../sql/database.sqlite") as db:
    df_products = db.read_table("Products")
    
df_products.tail()
# -


inspector_products = Inspector(df_products)
inspector_products

# The column `productName` is empty. There is one row which `productGroupName` is missing.

df_products[pd.isna(df_products["productGroupName"])]

# `productGroupName` describes a category of products and `productGroupCode` is its short name.

count_rows_by(df_products, by=["productGroupCode","productGroupName"])

# ## Environment

# %load_ext watermark
# %watermark -v -n -m -p numpy,scipy,sklearn,pandas,matplotlib,seaborn
