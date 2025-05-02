from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import db, User, Item, Subcategory, Attribute, ItemAttributeValue, Auction, Bid, Transaction, Notification, Alert
import json
from datetime import datetime, timezone

from sqlalchemy import and_, or_
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import func



seller_bp = Blueprint('seller', __name__)

# =======================================================================  
# Add New Item + Auction + Attributes + Notify Buyers for matching alerts
# ========================================================================
@seller_bp.route('/add-item', methods=['POST'])
@jwt_required()
def add_item():
    """
    API → Seller adds new item with required attribute values and optional auction setup.

    This endpoint allows a logged-in seller to:
    - Create a new item under a specified subcategory (subcategory_id is required)
    - Add core item details such as brand, model, title, condition, etc.
    - Attach dynamic attribute-value pairs to the item (e.g., RAM, Storage)
    - Automatically associate the item with its category (derived from subcategory)
    - (Optional) Initialize an auction if auction details are provided in the payload
    - Automatically notify buyers whose saved alerts match this item's criteria

    Validation ensures:
    - Only authenticated sellers can use this route
    - Attributes provided must match valid ones defined for the subcategory
    - Required fields like title and attributes are present

    If matching buyer alerts are found, structured notifications are sent in JSON format
    for frontend parsing (e.g., item_id, item_title, attributes, etc.).

    Returns:
        201 Created with newly created item ID
        400 Bad Request for validation errors
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user or user.Role != 'seller':
        return jsonify({'error': 'Seller access required'}), 403

    data = request.get_json()
    subcategory_id = data.get('subcategory_id')
    title = data.get('title')
    description = data.get('description')
    brand = data.get('brand')
    model = data.get('model')
    condition = data.get('condition')
    attributes = data.get('attributes', [])

    # Auction fields
    start_price = data.get('start_price')
    min_increment = data.get('min_increment')
    secret_min_price = data.get('secret_min_price')
    start_time = data.get('start_time')
    end_time = data.get('end_time')

    # Validate required fields
    if not (subcategory_id and title and attributes and start_price and min_increment and secret_min_price and start_time and end_time):
        return jsonify({'error': 'Missing required fields'}), 400

    subcategory = Subcategory.query.get(subcategory_id)
    if not subcategory:
        return jsonify({'error': 'Subcategory not found'}), 404

    category_id = subcategory.CategoryID

    # Create the Item
    new_item = Item(
        SubcategoryID=subcategory_id,
        CategoryID=category_id,
        OwnerID=user.UserID,
        Title=title,
        Description=description,
        Brand=brand,
        Model=model,
        Condition=condition,
        CreatedAt=datetime.now(timezone.utc)
    )
    db.session.add(new_item)
    db.session.flush()  # Get ItemID

    # Create Auction
    new_auction = Auction(
        ItemID=new_item.ItemID,
        StartPrice=start_price,
        MinIncrement=min_increment,
        SecretMinPrice=secret_min_price,
        StartTime=datetime.fromisoformat(start_time).astimezone(timezone.utc),
        EndTime=datetime.fromisoformat(end_time).astimezone(timezone.utc)
    )
    db.session.add(new_auction)

    # Insert Attribute Values
    for attr in attributes:
        attr_id = attr.get('attribute_id')
        value = attr.get('value')

        if not attr_id or not value:
            db.session.rollback()
            return jsonify({'error': 'Invalid attribute format'}), 400

        attribute = Attribute.query.get(attr_id)
        if not attribute or attribute.SubcategoryID != subcategory_id:
            db.session.rollback()
            return jsonify({'error': f'Attribute {attr_id} not valid for this subcategory'}), 400

        item_attr = ItemAttributeValue(ItemID=new_item.ItemID, AttributeID=attr_id, Value=value)
        db.session.add(item_attr)

        # Notify buyers with matching alerts
    subcat = Subcategory.query.get(subcategory_id)
    alerts = Alert.query.filter_by(Subcategory=subcat.Name).all()

    for alert in alerts:
        criteria = alert.SearchCriteria or {}
        match = True

        for field in ["Brand", "Model", "Condition"]:
            expected = criteria.get(field)

            if expected:
                expected_values = [value.lower() for value in expected]
                item_value = getattr(new_item, field, "").lower()

                if field in ["Brand", "Model"]:
                    # Partial match: any expected value should be a substring of the item_value
                    if not any(expected_val in item_value for expected_val in expected_values):
                        match = False
                        break
                else:
                    # Exact match for condition
                    if item_value not in expected_values:
                        match = False
                        break

        # Create notification if match is found
        if match:
            notif_payload = {
                "type": "item_alert_match",
                "title": "🔔 New item matched your alert",
                "item_id": new_item.ItemID,
                "item_title": new_item.Title, 
                "subcategory": subcat.Name,
                "brand": new_item.Brand,
                "model": new_item.Model,
                "condition": new_item.Condition,
                "start_time": new_auction.StartTime.isoformat(),
                "end_time": new_auction.EndTime.isoformat()
            }
            notification = Notification(
                UserID=alert.UserID,  # changed from ReceiverID to UserID
                Message=json.dumps(notif_payload),
                CreatedAt=datetime.now(timezone.utc)
            )
            db.session.add(notification)

    db.session.commit()

    return jsonify({
        'message': 'Item and auction added successfully',
        'item_id': new_item.ItemID,
        'auction_id': new_auction.AuctionID
    }), 201


# ================================
# View Seller's Items with Attributes + Auction Summary
# ================================
@seller_bp.route('/my-items', methods=['GET'])
@jwt_required()
def view_my_items():
    """API → Seller views all items including attribute values and auction summary"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user or user.Role != 'seller':
        return jsonify({'error': 'Seller access required'}), 403

    items = Item.query.filter_by(OwnerID=user.UserID).all()
    item_list = []

    for item in items:
        attrs = ItemAttributeValue.query.filter_by(ItemID=item.ItemID).all()
        attribute_data = [{
            "attribute_id": attr.AttributeID,
            "name": Attribute.query.get(attr.AttributeID).Name,
            "value": attr.Value
        } for attr in attrs]

        auction = Auction.query.filter_by(ItemID=item.ItemID).first()
        auction_data = None
        if auction:
            auction_data = {
                "AuctionID": auction.AuctionID,
                "StartPrice": float(auction.StartPrice),
                "MinIncrement": float(auction.MinIncrement),
                "StartTime": auction.StartTime.isoformat(),
                "EndTime": auction.EndTime.isoformat(),
                "IsClosed": auction.IsClosed,
                "SecretMinPrice": float(auction.SecretMinPrice)
            }

        item_list.append({
            "ItemID": item.ItemID,
            "Title": item.Title,
            "Description": item.Description,
            "Brand": item.Brand,
            "Model": item.Model,
            "Condition": item.Condition,
            "SubcategoryID": item.SubcategoryID,
            "CreatedAt": item.CreatedAt,
            "Attributes": attribute_data,
            "Auction": auction_data,
            "Status": item.Status
        })

    return jsonify({"items": item_list}), 200


# ================================
# Update Seller's Item + Optional Auction details + Optional Attributes
# ================================
@seller_bp.route('/update-item/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_item(item_id):
    """API → Seller updates item and optionally its attribute values"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user or user.Role != 'seller':
        return jsonify({'error': 'Seller access required'}), 403

    item = Item.query.get(item_id)
    if not item or item.OwnerID != user.UserID:
        return jsonify({'error': 'Unauthorized or item not found'}), 403

    data = request.get_json()
    if data.get('title'): item.Title = data['title']
    if data.get('description'): item.Description = data['description']
    if data.get('brand'): item.Brand = data['brand']
    if data.get('model'): item.Model = data['model']
    if data.get('condition'): item.Condition = data['condition']

    # Optional: Update auction if provided
    auction = Auction.query.filter_by(ItemID=item.ItemID).first()
    if auction:
        if data.get('start_price'): auction.StartPrice = data['start_price']
        if data.get('min_increment'): auction.MinIncrement = data['min_increment']
        if data.get('start_time'):
            auction.StartTime = datetime.fromisoformat(data['start_time']).replace(tzinfo=timezone.utc)
        if data.get('end_time'):
            auction.EndTime = datetime.fromisoformat(data['end_time']).replace(tzinfo=timezone.utc)
        if data.get('is_closed') is not None:  # Allow updating IsClosed
            auction.IsClosed = data['is_closed']
        # Note: Do NOT allow changing SecretMinPrice casually for security reasons


    attributes = data.get('attributes')
    if attributes:
        for attr in attributes:
            attr_id = attr.get('attribute_id')
            value = attr.get('value')

            existing = ItemAttributeValue.query.filter_by(ItemID=item_id, AttributeID=attr_id).first()
            if existing:
                existing.Value = value
            # else:
            #     # Optional: validate subcategory consistency
            #     attribute = Attribute.query.get(attr_id)
            #     if attribute and attribute.SubcategoryID == item.SubcategoryID:
            #         new_attr = ItemAttributeValue(ItemID=item_id, AttributeID=attr_id, Value=value)
            #         db.session.add(new_attr)

    db.session.commit()
    return jsonify({'message': 'Item and auction updated successfully'}), 200

# ================================
# Delete Seller's Item + Attributes
# ================================
@seller_bp.route('/delete-item/<int:item_id>', methods=['DELETE'])
@jwt_required()
def delete_item(item_id):
    """API → Seller deletes item and associated attributes"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user or user.Role != 'seller':
        return jsonify({'error': 'Seller access required'}), 403

    item = Item.query.get(item_id)
    if not item or item.OwnerID != user.UserID:
        return jsonify({'error': 'Item not found or unauthorized'}), 404

    # Delete all attribute values for this item
    ItemAttributeValue.query.filter_by(ItemID=item_id).delete()
    db.session.delete(item)
    db.session.commit()

    return jsonify({'message': 'Item and its attributes deleted successfully'}), 200

# ================================
# Accept Highest Bid
# ================================
@seller_bp.route('/accept-bid', methods=['POST'])
@jwt_required()
def accept_bid():
    """API → Seller accepts the highest bid and notifies the buyer"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user or user.Role != 'seller':
        return jsonify({'error': 'Seller access required'}), 403

    print("🔧 /accept-bid called")
    data = request.get_json()
    print("📥 Data received:", data)
    auction_id = data.get('auction_id')

    if not auction_id:
        print("DEBUG: Missing auction_id in request")
        return jsonify({'error': 'auction_id is required'}), 400

    auction = Auction.query.get(auction_id)
    if not auction or auction.IsClosed is False:
        print(f"DEBUG: Auction issue → Exists: {bool(auction)}, IsClosed: {getattr(auction, 'IsClosed', None)}")
        return jsonify({'error': 'Invalid or active auction'}), 400

    item = Item.query.get(auction.ItemID)
    if item.OwnerID != user.UserID:
        return jsonify({'error': 'Unauthorized'}), 403

    highest_bid = Bid.query.filter_by(AuctionID=auction.AuctionID).order_by(Bid.Amount.desc()).first()
    if not highest_bid:
        print("DEBUG: No bids found for this auction")
        return jsonify({'error': 'No bids to accept'}), 400

    transaction = Transaction(
        AuctionID=auction.AuctionID,
        BuyerID=highest_bid.BidderID,
        Price=highest_bid.Amount,
        TransactionDate=datetime.now(timezone.utc),
        Status='pending'
    )
    db.session.add(transaction)

    # Set item status as sold
    item.Status = 'sold'

    notification = Notification(
        UserID=highest_bid.BidderID,
        Message=json.dumps({
            "type": "payment_required",
            "transaction_id": transaction.TransactionID,
            "item_id": item.ItemID,
            "item_title": item.Title,
            "price": float(highest_bid.Amount)
        }),
        Status='unread'
    )
    db.session.add(notification)
    db.session.commit()

    return jsonify({'message': 'Bid accepted and buyer notified'}), 200


# ================================
# Extend Auction End Time
# ================================
@seller_bp.route('/extend-auction', methods=['POST'])
@jwt_required()
def extend_auction():
    """API → Seller extends the auction deadline for further bidding"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user or user.Role != 'seller':
        return jsonify({'error': 'Seller access required'}), 403

    data = request.get_json()
    auction_id = data.get('auction_id')
    new_end_time_str = data.get('new_end_time')

    if not auction_id or not new_end_time_str:
        return jsonify({'error': 'auction_id and new_end_time required'}), 400

    auction = Auction.query.get(auction_id)
    if not auction:
        return jsonify({'error': 'Invalid auction'}), 400

    item = Item.query.get(auction.ItemID)
    if item.OwnerID != user.UserID:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        # Parse new_end_time and ensure it is timezone-aware in UTC
        new_end_time = datetime.fromisoformat(new_end_time_str).astimezone(timezone.utc)
        print(new_end_time)
        if new_end_time <= datetime.now(timezone.utc):  # Standardized time
            return jsonify({'error': 'New end time must be in the future'}), 400
    except:
        return jsonify({'error': 'Invalid datetime format. Use ISO 8601 format (YYYY-MM-DDTHH:MM:SS).'}), 400

    auction.EndTime = new_end_time
    auction.IsClosed = False

    # Notify all previous bidders
    bidder_ids = db.session.query(Bid.BidderID).filter_by(AuctionID=auction.AuctionID).distinct()
    for bidder_id, in bidder_ids:
        notification = Notification(
            UserID=bidder_id,
            Message=f"Auction for item {item.Title} has been extended to {new_end_time_str}",
            CreatedAt=datetime.now(timezone.utc),  # Standardized time
            Status='unread'
        )
        db.session.add(notification)

    db.session.commit()
    return jsonify({'message': 'Auction extended and bidders notified'}), 200


# ================================
# Withdraw Item from Auction
# ================================
@seller_bp.route('/withdraw-item', methods=['POST'])
@jwt_required()
def withdraw_item():
    """API → Seller withdraws the item from the expired auction"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user or user.Role != 'seller':
        return jsonify({'error': 'Seller access required'}), 403

    data = request.get_json()
    auction_id = data.get('auction_id')

    if not auction_id:
        return jsonify({'error': 'auction_id is required'}), 400

    auction = Auction.query.get(auction_id)
    if not auction or auction.IsClosed is False:
        return jsonify({'error': 'Invalid or active auction'}), 400

    item = Item.query.get(auction.ItemID)
    if item.OwnerID != user.UserID:
        return jsonify({'error': 'Unauthorized'}), 403

    item.Status = 'withdrawn'
    auction.IsClosed = True

    db.session.commit()
    return jsonify({'message': 'Item withdrawn from auction'}), 200
