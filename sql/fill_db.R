#
# This code inserts raw data into the database.
# You have to create tables in advance.
# 

library(RSQLite)

csvs <- list(
          c("Customers","../data/customers.txt"),
          c("Products","../data/products.txt"),
          c("Campaigns","../data/campaigns.txt"),
          c("Orders","../data/orders.txt"),
          c("Orderlines","../data/orderlines.txt"))

dbh <- dbConnect(SQLite(),dbname="database.sqlite")

for (csv in csvs) {
  table <- csv[1]
  csv_path <- csv[2]
  cat(csv_path,"=>",table,"\n")
  
  df <- read.csv(csv_path, sep="\n", stringsAsFactors=F)
  dbWriteTable(dbh, table, df)
}

dbDisconnect(dbh)
