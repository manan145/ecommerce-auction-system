from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.dialects.mysql import ENUM

from . import db

# ==========================
# User Model
# ==========================
class User(db.Model):
    __tablename__ = 'User'

    UserID = db.Column(db.Integer, primary_key=True)
    Username = db.Column(db.String(50), nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    PasswordHash = db.Column(db.String(255), nullable=False)
    Role = db.Column(db.Enum('buyer', 'seller', 'customer_rep', 'admin'), nullable=False)
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)

# ==========================
# Category & Subcategory
# ==========================
class Category(db.Model):
    __tablename__ = 'Category'

    CategoryID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(50), nullable=False)

class Subcategory(db.Model):
    __tablename__ = 'Subcategory'

    SubcategoryID = db.Column(db.Integer, primary_key=True)
    CategoryID = db.Column(db.Integer, db.ForeignKey('Category.CategoryID'), nullable=False)
    Name = db.Column(db.String(50), nullable=False)

# ==========================
# Item Model
# ==========================
class Item(db.Model):
    __tablename__ = 'Item'

    ItemID = db.Column(db.Integer, primary_key=True)
    Brand = db.Column(db.String(50), nullable=False)
    Model = db.Column(db.String(100), nullable=False)
    Title = db.Column(db.String(100), nullable=False)
    Description = db.Column(db.Text)
    Condition = db.Column(ENUM(
        'New',
        'Refurbished',
        'Used',
        'Open Box',
        name='item_condition_enum'
    ), nullable=False)
    OwnerID = db.Column(db.Integer, db.ForeignKey('User.UserID'), nullable=False)
    CategoryID = db.Column(db.Integer, db.ForeignKey('Category.CategoryID'), nullable=False)
    SubcategoryID = db.Column(db.Integer, db.ForeignKey('Subcategory.SubcategoryID'), nullable=False)
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    Status = db.Column(db.Enum('active', 'withdrawn', 'sold'), default='active')

# ==========================
# Attribute & Item Attribute Value
# ==========================
class Attribute(db.Model):
    __tablename__ = 'Attribute'

    AttributeID = db.Column(db.Integer, primary_key=True)
    SubcategoryID = db.Column(db.Integer, db.ForeignKey('Subcategory.SubcategoryID'), nullable=False)
    Name = db.Column(db.String(50), nullable=False)

class ItemAttributeValue(db.Model):
    __tablename__ = 'ItemAttributeValue'

    ItemID = db.Column(db.Integer, db.ForeignKey('Item.ItemID'), primary_key=True)
    AttributeID = db.Column(db.Integer, db.ForeignKey('Attribute.AttributeID'), primary_key=True)
    Value = db.Column(db.String(100))

# ==========================
# Auction & Bid
# ==========================
class Auction(db.Model):
    __tablename__ = 'Auction'

    AuctionID = db.Column(db.Integer, primary_key=True)
    ItemID = db.Column(db.Integer, db.ForeignKey('Item.ItemID'), nullable=False)
    StartPrice = db.Column(db.Numeric(10, 2), nullable=False)
    MinIncrement = db.Column(db.Numeric(10, 2), nullable=False)
    SecretMinPrice = db.Column(db.Numeric(10, 2), nullable=False)
    StartTime = db.Column(db.DateTime, nullable=False)
    EndTime = db.Column(db.DateTime, nullable=False)
    IsClosed = db.Column(db.Boolean, default=False)

class Bid(db.Model):
    __tablename__ = 'Bid'

    BidID = db.Column(db.Integer, primary_key=True)
    AuctionID = db.Column(db.Integer, db.ForeignKey('Auction.AuctionID'), nullable=False)
    BidderID = db.Column(db.Integer, db.ForeignKey('User.UserID'), nullable=False)
    Amount = db.Column(db.Numeric(10, 2), nullable=False)
    BidTime = db.Column(db.DateTime, default=datetime.utcnow)
    MaxAutoBid = db.Column(db.Numeric(10, 2))
    Bidder = db.relationship('User', backref='bids', foreign_keys=[BidderID])

# ==========================
# Transaction
# ==========================
class Transaction(db.Model):
    __tablename__ = 'Transaction'

    TransactionID = db.Column(db.Integer, primary_key=True)
    AuctionID = db.Column(db.Integer, db.ForeignKey('Auction.AuctionID'), nullable=False)
    BuyerID = db.Column(db.Integer, db.ForeignKey('User.UserID'), nullable=False)
    Price = db.Column(db.Numeric(10, 2), nullable=False)
    TransactionDate = db.Column(db.DateTime, default=datetime.utcnow)
    Status = db.Column(db.Enum('completed', 'pending', 'cancelled'), default='completed')

# ==========================
# Feedback
# ==========================
class Feedback(db.Model):
    __tablename__ = 'Feedback'

    FeedbackID = db.Column(db.Integer, primary_key=True)
    FromUserID = db.Column(db.Integer, db.ForeignKey('User.UserID'), nullable=False)
    ToUserID = db.Column(db.Integer, db.ForeignKey('User.UserID'), nullable=False)
    Rating = db.Column(db.Integer, nullable=False)
    Comment = db.Column(db.Text)
    Date = db.Column(db.DateTime, default=datetime.utcnow)

# ==========================
# Message
# ==========================
class Message(db.Model):
    __tablename__ = 'Message'

    MessageID = db.Column(db.Integer, primary_key=True)
    SenderID = db.Column(db.Integer, db.ForeignKey('User.UserID'), nullable=False)
    ReceiverID = db.Column(db.Integer, db.ForeignKey('User.UserID'), nullable=False)
    Content = db.Column(db.Text, nullable=False)
    Timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# ==========================
# Alert
# ==========================
class Alert(db.Model):
    __tablename__ = 'Alert'

    AlertID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID'), nullable=False)
    Subcategory = db.Column(db.String(50), nullable=False)
    SearchCriteria = db.Column(db.JSON, nullable=False)
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)

# ==========================
# Watchlist
# ==========================
class Watchlist(db.Model):
    __tablename__ = 'Watchlist'

    WatchlistID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID'), nullable=False)
    AuctionID = db.Column(db.Integer, db.ForeignKey('Auction.AuctionID'), nullable=False)
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)

# ==========================
# Notification
# ==========================
class Notification(db.Model):
    __tablename__ = 'Notification'

    NotificationID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID'), nullable=False)
    Message = db.Column(db.String(255), nullable=False)
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    Status = db.Column(db.Enum('unread', 'read'), default='unread')

# ==========================
# Customer Representative
# ==========================
class CustomerRep(db.Model):
    __tablename__ = 'CustomerRep'

    RepID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID'), nullable=False)
    AssignedBy = db.Column(db.Integer, db.ForeignKey('User.UserID'))
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    Department = db.Column(db.String(50))
    Shift = db.Column(db.String(20))
    Status = db.Column(db.Enum('active', 'inactive'), default='active')

# ==========================
# Admin
# ==========================
class Admin(db.Model):
    __tablename__ = 'Admin'

    AdminID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID'), nullable=False, unique=True)
    AccessLevel = db.Column(db.Enum('SuperAdmin', 'Manager', 'ReadOnly'), nullable=False)
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    LastLogin = db.Column(db.DateTime)

# ==========================
# Customer Query
# ==========================

class CustomerQuery(db.Model):
    __tablename__ = 'CustomerQuery'

    QueryID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID'), nullable=False)
    Subject = db.Column(db.String(255), nullable=False)
    Message = db.Column(db.Text, nullable=False)
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    Status = db.Column(db.Enum('open', 'closed'), default='open')