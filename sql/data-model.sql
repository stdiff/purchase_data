-- 
-- 
-- 

DROP TABLE IF EXISTS Customers;

CREATE TABLE IF NOT EXISTS Customers(
  customerId  INTEGER PRIMARY KEY,
  householdId INTEGER,
  gender      TEXT,
  firstName   TEXT
);

-- 
-- 
-- 

DROP TABLE IF EXISTS Products;

CREATE TABLE IF NOT EXISTS Products(
  productId        INTEGER PRIMARY KEY,
  productName      TEXT, 
  productGroupCode TEXT, 
  productGroupName TEXT, 
  inStockFlag      TEXT, 
  fullPrice        INTEGER
);

-- 
-- 
-- 

DROP TABLE IF EXISTS Campaigns;

CREATE TABLE IF NOT EXISTS Campaigns(
  campaignId       INTEGER PRIMARY KEY,
  campaignName     TEXT,
  channel          TEXT,
  discount         INTEGER,
  freeShippingFlag TEXT
);

-- 
-- 
-- 

DROP TABLE IF EXISTS Orders;

CREATE TABLE IF NOT EXISTS Orders(
  orderId       INTEGER PRIMARY KEY,
  customerId    INTEGER,
  campaignId    INTEGER,
  orderDate     DATETIME,
  city          TEXT,
  state         TEXT,
  zipCode       TEXT,
  paymentType   TEXT,
  totalPrice    REAL,
  numOrderlines INTEGER,
  numUnits      INTEGER,
  FOREIGN KEY (customerId) REFERENCES Customers(customerId),
  FOREIGN KEY (campaignId) REFERENCES Campaigns(campaignId)
);

-- 
-- 
-- 

DROP TABLE IF EXISTS Orderlines;

CREATE TABLE IF NOT EXISTS Orderlines(
  orderlineId INTEGER PRIMARY KEY,
  orderId     INTEGER NOT NULL,
  productId   INTEGER,
  shipDate    DATETIME,
  billDate    DATETIME,
  unitPrice   REAL,
  numUnits    INTEGER,
  totalPrice  REAL,
  FOREIGN KEY (orderId) REFERENCES Orders(orderId),
  FOREIGN KEY (productId) REFERENCES Products(productId)
);


