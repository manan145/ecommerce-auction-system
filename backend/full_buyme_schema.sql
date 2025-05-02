
-- SQL script for table creation (BuyMe project schema)

-- User Table

use buyme_auction; 

CREATE TABLE User (
    UserID INT AUTO_INCREMENT PRIMARY KEY,
    Username VARCHAR(50) NOT NULL,
    Email VARCHAR(100) NOT NULL UNIQUE,
    PasswordHash VARCHAR(255) NOT NULL,
    Role ENUM('buyer', 'seller', 'customer_rep', 'admin') NOT NULL,
    CreatedAt DATETIME
);

-- Category & Subcategory
CREATE TABLE Category (
    CategoryID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(50) NOT NULL
);

CREATE TABLE Subcategory (
    SubcategoryID INT AUTO_INCREMENT PRIMARY KEY,
    CategoryID INT NOT NULL,
    Name VARCHAR(50) NOT NULL,
    FOREIGN KEY (CategoryID) REFERENCES Category(CategoryID) ON DELETE CASCADE
);

-- Item
CREATE TABLE Item (
    ItemID INT AUTO_INCREMENT PRIMARY KEY,
    Brand VARCHAR(50) NOT NULL,
    Model VARCHAR(100) NOT NULL,
    Title VARCHAR(100) NOT NULL,
    Description TEXT,
    `Condition` ENUM('New', 'Refurbished', 'Used', 'Open Box') NOT NULL,
    OwnerID INT NOT NULL,
    CategoryID INT NOT NULL,
    SubcategoryID INT NOT NULL,
    CreatedAt DATETIME,
    Status ENUM('active', 'withdrawn', 'sold') DEFAULT 'active' NOT NULL,
    FOREIGN KEY (OwnerID) REFERENCES User(UserID) ON DELETE CASCADE,
    FOREIGN KEY (CategoryID) REFERENCES Category(CategoryID) ON DELETE CASCADE,
    FOREIGN KEY (SubcategoryID) REFERENCES Subcategory(SubcategoryID) ON DELETE CASCADE
);

-- Attribute & ItemAttributeValue
CREATE TABLE Attribute (
    AttributeID INT AUTO_INCREMENT PRIMARY KEY,
    SubcategoryID INT NOT NULL,
    Name VARCHAR(50) NOT NULL,
    FOREIGN KEY (SubcategoryID) REFERENCES Subcategory(SubcategoryID) ON DELETE CASCADE
);

CREATE TABLE ItemAttributeValue (
    ItemID INT NOT NULL,
    AttributeID INT NOT NULL,
    Value VARCHAR(100),
    PRIMARY KEY (ItemID, AttributeID),
    FOREIGN KEY (ItemID) REFERENCES Item(ItemID) ON DELETE CASCADE,
    FOREIGN KEY (AttributeID) REFERENCES Attribute(AttributeID) ON DELETE CASCADE
);

-- Auction & Bid
CREATE TABLE Auction (
    AuctionID INT AUTO_INCREMENT PRIMARY KEY,
    ItemID INT NOT NULL,
    StartPrice DECIMAL(10,2) NOT NULL,
    MinIncrement DECIMAL(10,2) NOT NULL,
    SecretMinPrice DECIMAL(10,2) NOT NULL,
    StartTime DATETIME NOT NULL,
    EndTime DATETIME NOT NULL,
    IsClosed BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (ItemID) REFERENCES Item(ItemID) ON DELETE CASCADE
);

CREATE TABLE Bid (
    BidID INT AUTO_INCREMENT PRIMARY KEY,
    AuctionID INT NOT NULL,
    BidderID INT NOT NULL,
    Amount DECIMAL(10,2) NOT NULL,
    BidTime DATETIME,
    MaxAutoBid DECIMAL(10,2),
    FOREIGN KEY (AuctionID) REFERENCES Auction(AuctionID) ON DELETE CASCADE,
    FOREIGN KEY (BidderID) REFERENCES User(UserID) ON DELETE CASCADE
);

-- Transaction
CREATE TABLE Transaction (
    TransactionID INT AUTO_INCREMENT PRIMARY KEY,
    AuctionID INT NOT NULL,
    BuyerID INT NOT NULL,
    Price DECIMAL(10,2) NOT NULL,
    TransactionDate DATETIME,
    Status ENUM('completed', 'pending', 'cancelled') DEFAULT 'completed',
    FOREIGN KEY (AuctionID) REFERENCES Auction(AuctionID) ON DELETE CASCADE,
    FOREIGN KEY (BuyerID) REFERENCES User(UserID) ON DELETE CASCADE
);

-- Alert
CREATE TABLE Alert (
    AlertID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT NOT NULL,
    Category VARCHAR(50) NOT NULL,
    Subcategory VARCHAR(50) NOT NULL,
    SearchCriteria JSON NOT NULL,
    CreatedAt DATETIME,
    FOREIGN KEY (UserID) REFERENCES User(UserID) ON DELETE CASCADE
);

-- Notification
CREATE TABLE Notification (
    NotificationID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT NOT NULL,
    Message TEXT NOT NULL,
    CreatedAt DATETIME,
    Status ENUM('unread', 'read') DEFAULT 'unread',
    FOREIGN KEY (UserID) REFERENCES User(UserID) ON DELETE CASCADE
);

-- Customer Representative
CREATE TABLE CustomerRep (
    RepID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT NOT NULL,
    AssignedBy INT,
    CreatedAt DATETIME,
    Department VARCHAR(50),
    Shift VARCHAR(20),
    Status ENUM('active', 'inactive') DEFAULT 'active',
    FOREIGN KEY (UserID) REFERENCES User(UserID) ON DELETE CASCADE,
    FOREIGN KEY (AssignedBy) REFERENCES User(UserID) ON DELETE CASCADE
);

-- Admin
CREATE TABLE Admin (
    AdminID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT NOT NULL UNIQUE,
    AccessLevel ENUM('SuperAdmin', 'Manager', 'ReadOnly') NOT NULL,
    CreatedAt DATETIME,
    LastLogin DATETIME,
    FOREIGN KEY (UserID) REFERENCES User(UserID) ON DELETE CASCADE
);

-- Customer Query
CREATE TABLE CustomerQuery (
    QueryID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT NOT NULL,
    Subject VARCHAR(100) NOT NULL,
    Message TEXT NOT NULL,
    Response TEXT,
    ResponseBy INT,
    ResponseAt DATETIME,
    CreatedAt DATETIME,
    Status ENUM('open', 'closed') DEFAULT 'open',
    FOREIGN KEY (UserID) REFERENCES User(UserID) ON DELETE CASCADE,
    FOREIGN KEY (ResponseBy) REFERENCES User(UserID) ON DELETE CASCADE
);

-- FAQ
CREATE TABLE FAQ (
    FAQID INT AUTO_INCREMENT PRIMARY KEY,
    Question TEXT NOT NULL,
    Answer TEXT NOT NULL
);
