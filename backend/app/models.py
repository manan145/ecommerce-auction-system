from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
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
    CreatedAt = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

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
    CategoryID = db.Column(db.Integer, db.ForeignKey('Category.CategoryID', ondelete="CASCADE"), nullable=False)
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
    OwnerID = db.Column(db.Integer, db.ForeignKey('User.UserID', ondelete="CASCADE"), nullable=False)
    CategoryID = db.Column(db.Integer, db.ForeignKey('Category.CategoryID', ondelete="CASCADE"), nullable=False)
    SubcategoryID = db.Column(db.Integer, db.ForeignKey('Subcategory.SubcategoryID', ondelete="CASCADE"), nullable=False)
    CreatedAt = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    Status = db.Column(db.Enum('active', 'withdrawn', 'sold'), default='active', nullable=False)

# ==========================
# Attribute & Item Attribute Value
# ==========================
class Attribute(db.Model):
    __tablename__ = 'Attribute'

    AttributeID = db.Column(db.Integer, primary_key=True)
    SubcategoryID = db.Column(db.Integer, db.ForeignKey('Subcategory.SubcategoryID', ondelete="CASCADE"), nullable=False)
    Name = db.Column(db.String(50), nullable=False)

class ItemAttributeValue(db.Model):
    __tablename__ = 'ItemAttributeValue'

    ItemID = db.Column(db.Integer, db.ForeignKey('Item.ItemID', ondelete="CASCADE"), primary_key=True)
    AttributeID = db.Column(db.Integer, db.ForeignKey('Attribute.AttributeID', ondelete="CASCADE"), primary_key=True)
    Value = db.Column(db.String(100))

# ==========================
# Auction & Bid
# ==========================
class Auction(db.Model):
    __tablename__ = 'Auction'

    AuctionID = db.Column(db.Integer, primary_key=True)
    ItemID = db.Column(db.Integer, db.ForeignKey('Item.ItemID', ondelete="CASCADE"), nullable=False)
    StartPrice = db.Column(db.Numeric(10, 2), nullable=False)
    MinIncrement = db.Column(db.Numeric(10, 2), nullable=False)
    SecretMinPrice = db.Column(db.Numeric(10, 2), nullable=False)
    StartTime = db.Column(db.DateTime(timezone=True), nullable=False)
    EndTime = db.Column(db.DateTime(timezone=True), nullable=False)
    IsClosed = db.Column(db.Boolean, default=False)

class Bid(db.Model):
    __tablename__ = 'Bid'

    BidID = db.Column(db.Integer, primary_key=True)
    AuctionID = db.Column(db.Integer, db.ForeignKey('Auction.AuctionID', ondelete="CASCADE"), nullable=False)
    BidderID = db.Column(db.Integer, db.ForeignKey('User.UserID', ondelete="CASCADE"), nullable=False)
    Amount = db.Column(db.Numeric(10, 2), nullable=False)
    BidTime = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    MaxAutoBid = db.Column(db.Numeric(10, 2))
    Bidder = db.relationship('User', backref='bids', foreign_keys=[BidderID])

# ==========================
# Transaction
# ==========================
class Transaction(db.Model):
    __tablename__ = 'Transaction'

    TransactionID = db.Column(db.Integer, primary_key=True)
    AuctionID = db.Column(db.Integer, db.ForeignKey('Auction.AuctionID', ondelete="CASCADE"), nullable=False)
    BuyerID = db.Column(db.Integer, db.ForeignKey('User.UserID', ondelete="CASCADE"), nullable=False)
    Price = db.Column(db.Numeric(10, 2), nullable=False)
    TransactionDate = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    Status = db.Column(db.Enum('completed', 'pending', 'cancelled'), default='completed')


# ==========================
# Alert
# ==========================
class Alert(db.Model):
    __tablename__ = 'Alert'

    AlertID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID', ondelete="CASCADE"), nullable=False)
    Category = db.Column(db.String(50), nullable=False)
    Subcategory = db.Column(db.String(50), nullable=False)
    SearchCriteria = db.Column(db.JSON, nullable=False)
    CreatedAt = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

# ==========================
# Notification
# ==========================
class Notification(db.Model):
    __tablename__ = 'Notification'

    NotificationID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID', ondelete="CASCADE"), nullable=False)
    Message = db.Column(db.String(255), nullable=False)
    CreatedAt = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    Status = db.Column(db.Enum('unread', 'read'), default='unread')

# ==========================
# Customer Representative
# ==========================
class CustomerRep(db.Model):
    __tablename__ = 'CustomerRep'

    RepID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID', ondelete="CASCADE"), nullable=False)
    AssignedBy = db.Column(db.Integer, db.ForeignKey('User.UserID', ondelete="CASCADE"))
    CreatedAt = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    Department = db.Column(db.String(50))
    Shift = db.Column(db.String(20))
    Status = db.Column(db.Enum('active', 'inactive'), default='active')

# ==========================
# Admin
# ==========================
class Admin(db.Model):
    __tablename__ = 'Admin'

    AdminID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID', ondelete="CASCADE"), nullable=False, unique=True)
    AccessLevel = db.Column(db.Enum('SuperAdmin', 'Manager', 'ReadOnly'), nullable=False)
    CreatedAt = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    LastLogin = db.Column(db.DateTime(timezone=True))

# ==========================
# Customer Query
# ==========================
class CustomerQuery(db.Model):
    __tablename__ = 'CustomerQuery'

    QueryID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID', ondelete="CASCADE"), nullable=False)
    Subject = db.Column(db.String(100), nullable=False)
    Message = db.Column(db.Text, nullable=False)
    Response = db.Column(db.Text)
    ResponseBy = db.Column(db.Integer, db.ForeignKey('User.UserID', ondelete="CASCADE"))
    ResponseAt = db.Column(db.DateTime(timezone=True))   
    CreatedAt = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    Status = db.Column(db.Enum('open', 'closed'), default='open')



class FAQ(db.Model):
    __tablename__ = 'FAQ'

    FAQID = db.Column(db.Integer, primary_key=True)
    Question = db.Column(db.Text, nullable=False)
    Answer = db.Column(db.Text, nullable=False)

