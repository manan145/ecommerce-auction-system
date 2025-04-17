from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from ..models import *
from datetime import datetime
from ..utils.filter_utils import filter_items  # Reusable filtering logic

public_bp = Blueprint('public', __name__)

# -----------------------------------------------
# GET /browse/categories
# Returns all categories
# -----------------------------------------------
@public_bp.route('/browse/categories', methods=['GET'])
def list_categories():
    categories = Category.query.all()
    result = [{"CategoryID": cat.CategoryID, "Name": cat.Name} for cat in categories]
    return jsonify(result), 200

# -----------------------------------------------
# GET /browse/subcategories/<category_id>
# Returns subcategories under a category given its ID
# -----------------------------------------------
@public_bp.route('/browse/subcategories/<int:category_id>', methods=['GET'])
def list_subcategories(category_id):
    category = Category.query.get(category_id)
    if not category:
        return jsonify({"error": "Category not found"}), 404

    subcategories = Subcategory.query.filter_by(CategoryID=category.CategoryID).all()
    result = [{"SubcategoryID": sub.SubcategoryID, "Name": sub.Name} for sub in subcategories]
    return jsonify(result), 200

# -----------------------------------------------
# GET /browse/items/<int:subcategory_id>?seller_only=true
# Returns items in a subcategory given its ID, optionally filtered by current seller
# -----------------------------------------------
@public_bp.route('/browse/items/<int:subcategory_id>', methods=['GET'])
@jwt_required(optional=True)
def list_items_by_subcategory(subcategory_id):
    user_id = get_jwt_identity()
    seller_only = request.args.get('seller_only', 'false').lower() == 'true'

    subcategory = Subcategory.query.get(subcategory_id)
    if not subcategory:
        return jsonify({"error": "Subcategory not found"}), 404

    query = Item.query.filter(Item.SubcategoryID == subcategory.SubcategoryID)
    if seller_only and user_id:
        query = query.filter(Item.OwnerID == user_id)

    items = query.all()
    result = []

    for item in items:
        attrs = ItemAttributeValue.query.filter_by(ItemID=item.ItemID).all()
        attr_data = [{
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
                "IsClosed": auction.IsClosed
            }
            if user_id == item.OwnerID:  # Seller can view SecretMinPrice
                auction_data["SecretMinPrice"] = float(auction.SecretMinPrice)

        result.append({
            "ItemID": item.ItemID,
            "Title": item.Title,
            "Brand": item.Brand,
            "Model": item.Model,
            "Condition": item.Condition,
            "SubcategoryID": item.SubcategoryID,
            "CreatedAt": item.CreatedAt,
            "OwnerID": item.OwnerID,
            "Attributes": attr_data,
            "Auction": auction_data
        })

    return jsonify(result), 200

# -----------------------------------------------
# POST /browse/search-items
# Search all items with filters (optional seller-only toggle)
# -----------------------------------------------
from flask import json
@public_bp.route('/browse/search-items', methods=['POST'])
@jwt_required(optional=True)
def public_search_items():
    try:
        raw_data = request.get_data(as_text=True)
        print("📦 Raw request data:", raw_data)

        data = request.get_json()
        print("✅ Parsed data:", data)
        print("🔎 Data type:", type(data))

        filters = data.get('filters', {})
        sort_by = data.get('sort_by', 'created_desc')
        offset = int(data.get('offset', 0))
        limit = int(data.get('limit', 20))

        user_id = get_jwt_identity()
        only_my_items = data.get('only_my_items', False) and user_id is not None

        auction_filters = data.get('auction_filters', {})
        min_price = auction_filters.get('min_price')
        max_price = auction_filters.get('max_price')
        is_closed = auction_filters.get('is_closed')

        result_data = filter_items(
            filters=filters,
            only_my_items=only_my_items,
            user_id=user_id,
            sort_by=sort_by,
            offset=offset,
            limit=limit,
            auction_filters={
                'min_price': min_price,
                'max_price': max_price,
                'is_closed': is_closed
            }
        )

        items = result_data.get("results", [])

        for item in items:
            print("🧪 Item in results:", item, "| Type:", type(item))
            if not isinstance(item, dict):
                print("⚠️ Skipping item — not a dict.")
                continue

            auction = Auction.query.filter_by(ItemID=item["ItemID"]).first()
            if auction:
                auction_data = {
                    "AuctionID": auction.AuctionID,
                    "StartPrice": float(auction.StartPrice),
                    "MinIncrement": float(auction.MinIncrement),
                    "StartTime": auction.StartTime.isoformat(),
                    "EndTime": auction.EndTime.isoformat(),
                    "IsClosed": auction.IsClosed
                }
                if only_my_items:
                    auction_data["SecretMinPrice"] = float(auction.SecretMinPrice)
                item["Auction"] = auction_data

        return jsonify(items), 200

    except Exception as e:
        print("🔥 Error in public_search_items:", str(e))
        return jsonify({"error": "Internal server error"}), 500

@public_bp.route('/browse/attributes/<int:subcategory_id>', methods=['GET'])
def get_attributes_by_subcategory(subcategory_id):
    attributes = Attribute.query.filter_by(SubcategoryID=subcategory_id).all()
    
    if not attributes:
        return jsonify({"message": "No attributes found for this subcategory."}), 404

    result = [{
        "AttributeID": attr.AttributeID,
        "Name": attr.Name
    } for attr in attributes]

    return jsonify(result), 200

@public_bp.route('/browse/attribute-values/<int:attribute_id>', methods=['GET'])
def get_attribute_values(attribute_id):
    values = (
        db.session.query(ItemAttributeValue.Value)
        .filter_by(AttributeID=attribute_id)
        .distinct()
        .all()
    )
    value_list = [v[0] for v in values]
    return jsonify(value_list), 200

# ==========================================
# Customer Query Submission
# ==========================================
@public_bp.route('/customer-query', methods=['POST'])
@jwt_required()
def submit_customer_query():
    """
    Users (buyers/sellers) submit support queries.
    """
    user_id = get_jwt_identity()
    data = request.get_json()
    subject = data.get('subject')
    message = data.get('message')

    if not subject or not message:
        return jsonify({'error': 'Subject and message required'}), 400

    new_query = CustomerQuery(
        UserID=user_id,
        Subject=subject,
        Message=message,
        Status='open'
    )
    db.session.add(new_query)
    db.session.commit()
    return jsonify({'message': 'Query submitted'}), 201

# ==========================================    
# Message Sending
# ==========================================
@public_bp.route('/messages/send', methods=['POST'])
@jwt_required()
def send_message():
    """
    Send a message to another user (e.g., rep responding to query)
    """
    sender_id = get_jwt_identity()
    data = request.get_json()
    receiver_id = data.get('receiver_id')
    content = data.get('content')

    if not receiver_id or not content:
        return jsonify({'error': 'Receiver ID and content required'}), 400

    message = Message(SenderID=sender_id, ReceiverID=receiver_id, Content=content)
    db.session.add(message)

    notification = Notification(
        UserID=receiver_id,
        Message=json.dumps({
            "type": "new_message",
            "from_user_id": sender_id,
            "content_preview": content[:50],  # Short preview
            "timestamp": datetime.now(datetime.timezone.utc).isoformat()
        }),
        CreatedAt=datetime.now(datetime.timezone.utc).isoformat()
    )
    db.session.add(notification)

    db.session.commit()
    return jsonify({'message': 'Message sent'}), 201

# ==========================================
# Get Message Thread
# ==========================================
@public_bp.route('/messages/thread/<int:user_id>', methods=['GET'])
@jwt_required()
def get_thread(user_id):
    """
    Fetch threaded conversation between current user and user_id
    """
    current_user_id = get_jwt_identity()

    thread = Message.query.filter(
        ((Message.SenderID == current_user_id) & (Message.ReceiverID == user_id)) |
        ((Message.SenderID == user_id) & (Message.ReceiverID == current_user_id))
    ).order_by(Message.Timestamp.asc()).all()

    return jsonify([{
        'SenderID': msg.SenderID,
        'ReceiverID': msg.ReceiverID,
        'Content': msg.Content,
        'Timestamp': msg.Timestamp.isoformat()
    } for msg in thread]), 200

# ==========================================
# Get Last Message from Each Sender
# ==========================================
@public_bp.route('/messages/last-from-each-sender', methods=['GET'])
@jwt_required()
def get_last_messages_by_sender():
    """
    API → Get the latest message from each sender to the current receiver,
    sorted by most recent timestamp (like WhatsApp chat list).

    Returns:
        JSON list of latest messages grouped by sender, ordered by most recent first
    """
    current_user_id = get_jwt_identity()

    from sqlalchemy import func, and_
    
    # Subquery: latest message timestamp per sender to this receiver
    subquery = db.session.query(
        Message.SenderID,
        func.max(Message.Timestamp).label('LatestTime')
    ).filter(Message.ReceiverID == current_user_id)\
     .group_by(Message.SenderID).subquery()

    # Join with Message to fetch the actual message contents
    latest_messages = db.session.query(Message)\
        .join(subquery, and_(
            Message.SenderID == subquery.c.SenderID,
            Message.Timestamp == subquery.c.LatestTime
        )).order_by(Message.Timestamp.desc()).all()

    result = [{
        "SenderID": msg.SenderID,
        "MessageID": msg.MessageID,
        "Content": msg.Content,
        "Timestamp": msg.Timestamp.isoformat()
    } for msg in latest_messages]

    return jsonify(result), 200