CREATE TABLE User (
    UserID INT PRIMARY KEY AUTO_INCREMENT,
    Username VARCHAR(50) NOT NULL,
    Email VARCHAR(100) NOT NULL UNIQUE,
    PasswordHash VARCHAR(255) NOT NULL,
    Role ENUM('buyer', 'seller', 'customer_rep', 'admin') NOT NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Category (
    CategoryID INT PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(50) NOT NULL
);

CREATE TABLE Subcategory (
    SubcategoryID INT PRIMARY KEY AUTO_INCREMENT,
    CategoryID INT NOT NULL,
    Name VARCHAR(50) NOT NULL,
    FOREIGN KEY (CategoryID) REFERENCES Category(CategoryID)
);

CREATE TABLE Item (
    ItemID INT PRIMARY KEY AUTO_INCREMENT,
    Title VARCHAR(100) NOT NULL,
    Brand VARCHAR(50) NOT NULL,
    Model VARCHAR(100) NOT NULL,
    `Condition` ENUM('New', 'Open Box', 'Refurbished', 'Used'),
    Description TEXT,
    OwnerID INT NOT NULL,
    CategoryID INT NOT NULL,
    SubcategoryID INT NOT NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status ENUM('active', 'withdrawn', 'sold') DEFAULT 'active',
    FOREIGN KEY (OwnerID) REFERENCES User(UserID),
    FOREIGN KEY (CategoryID) REFERENCES Category(CategoryID),
    FOREIGN KEY (SubcategoryID) REFERENCES Subcategory(SubcategoryID)
);

CREATE TABLE Attribute (
    AttributeID INT PRIMARY KEY AUTO_INCREMENT,
    SubcategoryID INT NOT NULL,
    Name VARCHAR(50) NOT NULL,
    FOREIGN KEY (SubcategoryID) REFERENCES Subcategory(SubcategoryID)
);

CREATE TABLE ItemAttributeValue (
    ItemID INT NOT NULL,
    AttributeID INT NOT NULL,
    Value VARCHAR(100),
    PRIMARY KEY (ItemID, AttributeID),
    FOREIGN KEY (ItemID) REFERENCES Item(ItemID),
    FOREIGN KEY (AttributeID) REFERENCES Attribute(AttributeID)
);

CREATE TABLE Auction (
    AuctionID INT PRIMARY KEY AUTO_INCREMENT,
    ItemID INT NOT NULL,
    StartPrice DECIMAL(10,2) NOT NULL,
    MinIncrement DECIMAL(10,2) NOT NULL,
    SecretMinPrice DECIMAL(10,2) NOT NULL,
    StartTime DATETIME NOT NULL,
    EndTime DATETIME NOT NULL,
    IsClosed BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (ItemID) REFERENCES Item(ItemID)
);

CREATE TABLE Bid (
    BidID INT PRIMARY KEY AUTO_INCREMENT,
    AuctionID INT NOT NULL,
    BidderID INT NOT NULL,
    Amount DECIMAL(10,2) NOT NULL,
    BidTime DATETIME DEFAULT CURRENT_TIMESTAMP,
    MaxAutoBid DECIMAL(10,2),
    FOREIGN KEY (AuctionID) REFERENCES Auction(AuctionID),
    FOREIGN KEY (BidderID) REFERENCES User(UserID)
);

CREATE TABLE Transaction (
    TransactionID INT PRIMARY KEY AUTO_INCREMENT,
    AuctionID INT NOT NULL,
    BuyerID INT NOT NULL,
    Price DECIMAL(10,2) NOT NULL,
    TransactionDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    Status ENUM('completed', 'pending', 'cancelled') DEFAULT 'completed',
    FOREIGN KEY (AuctionID) REFERENCES Auction(AuctionID),
    FOREIGN KEY (BuyerID) REFERENCES User(UserID)
);

CREATE TABLE Feedback (
    FeedbackID INT PRIMARY KEY AUTO_INCREMENT,
    FromUserID INT NOT NULL,
    ToUserID INT NOT NULL,
    Rating INT NOT NULL,
    Comment TEXT,
    Date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (FromUserID) REFERENCES User(UserID),
    FOREIGN KEY (ToUserID) REFERENCES User(UserID)
);

CREATE TABLE Message (
    MessageID INT PRIMARY KEY AUTO_INCREMENT,
    SenderID INT NOT NULL,
    ReceiverID INT NOT NULL,
    Content TEXT NOT NULL,
    Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (SenderID) REFERENCES User(UserID),
    FOREIGN KEY (ReceiverID) REFERENCES User(UserID)
);

CREATE TABLE Alert (
    AlertID INT PRIMARY KEY AUTO_INCREMENT,
    UserID INT NOT NULL,
    Subcategory VARCHAR(50) NOT NULL,
    SearchCriteria JSON NOT NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (UserID) REFERENCES User(UserID)
);

CREATE TABLE Watchlist (
    WatchlistID INT PRIMARY KEY AUTO_INCREMENT,
    UserID INT NOT NULL,
    AuctionID INT NOT NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (UserID) REFERENCES User(UserID),
    FOREIGN KEY (AuctionID) REFERENCES Auction(AuctionID)
);

CREATE TABLE Notification (
    NotificationID INT PRIMARY KEY AUTO_INCREMENT,
    UserID INT NOT NULL,
    Message VARCHAR(255) NOT NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status ENUM('unread', 'read') DEFAULT 'unread',
    FOREIGN KEY (UserID) REFERENCES User(UserID)
);

CREATE TABLE CustomerRep (
    RepID INT PRIMARY KEY AUTO_INCREMENT,
    UserID INT NOT NULL,
    AssignedBy INT,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Department VARCHAR(50),
    Shift VARCHAR(20),
    Status ENUM('active', 'inactive') DEFAULT 'active',
    FOREIGN KEY (UserID) REFERENCES User(UserID),
    FOREIGN KEY (AssignedBy) REFERENCES User(UserID)
);

CREATE TABLE Admin (
    AdminID INT PRIMARY KEY AUTO_INCREMENT,
    UserID INT NOT NULL,
    AccessLevel ENUM('SuperAdmin', 'Manager', 'ReadOnly') NOT NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    LastLogin DATETIME,
    FOREIGN KEY (UserID) REFERENCES User(UserID)
);