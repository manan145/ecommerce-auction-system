from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from ..models import *
from datetime import datetime, timedelta
from sqlalchemy import func, or_, and_
from ..utils.filter_utils import filter_items  # Reusable filtering logic
from fuzzywuzzy import fuzz
import re

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
        data = request.get_json()


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
            if not isinstance(item, dict):
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

@public_bp.route('/customer-query/mine', methods=['GET'])
@jwt_required()
def get_my_queries():
    """
    Returns all queries submitted by the currently logged-in user,
    including rep responses, responder name, response time, and status.
    """
    user_id = get_jwt_identity()

    queries = db.session.query(
        CustomerQuery,
        User.Username.label('ResponderName')
    ).outerjoin(User, CustomerQuery.ResponseBy == User.UserID)\
     .filter(CustomerQuery.UserID == user_id)\
     .order_by(CustomerQuery.CreatedAt.desc()).all()

    result = []
    for query, responder_name in queries:
        result.append({
            'QueryID': query.QueryID,
            'Subject': query.Subject,
            'Message': query.Message,
            'Status': query.Status,
            'CreatedAt': query.CreatedAt.isoformat(),
            'Response': query.Response,
            'ResponderName': responder_name,
            'ResponseAt': query.ResponseAt.isoformat() if query.ResponseAt else None
        })

    return jsonify(result), 200

# ==========================================
# Get Similar Auctions
# ==========================================
@public_bp.route('/auctions/similar/<int:auction_id>', methods=['GET'])
@jwt_required()
def get_smarter_similar_auctions(auction_id):
    now = datetime.now(timezone.utc)
    first_day_this_month = now.replace(day=1)
    last_day_prev_month = first_day_this_month - timedelta(days=1)
    first_day_prev_month = last_day_prev_month.replace(day=1)

    # Fetch the current auction and item
    auction = Auction.query.get(auction_id)
    if not auction:
        return jsonify({"error": "Auction not found"}), 404

    item = Item.query.get(auction.ItemID)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    # Extract title keywords and brand for fuzzy match
    title_keywords = [word.strip().lower() for word in item.Title.split() if len(word) > 2]
    brand = item.Brand.lower() if item.Brand else ""

    # Build keyword filters using ILIKE
    keyword_filters = [Item.Title.ilike(f"%{kw}%") for kw in title_keywords]

    # Query: same subcategory, closed, ended within last month, not the same auction
    similar_query = (
        db.session.query(Auction, Item)
        .join(Item, Item.ItemID == Auction.ItemID)
        .filter(
            Auction.AuctionID != auction_id,
            Auction.IsClosed == True,
            Auction.EndTime >= first_day_prev_month,
            Auction.EndTime <= last_day_prev_month,
            Item.SubcategoryID == item.SubcategoryID,
            or_(
                func.lower(Item.Brand).ilike(f"%{brand}%"),
                *keyword_filters
            )
        )
        .order_by(Auction.EndTime.desc())
        .limit(10)
    )

    similar_auctions = similar_query.all()

    results = []
    for auct, itm in similar_auctions:
        final_transaction = (
            Transaction.query
            .filter_by(AuctionID=auct.AuctionID, Status="completed")
            .order_by(Transaction.TransactionDate.desc())
            .first()
        )

        results.append({
            "item_id": itm.ItemID,
            "title": itm.Title,
            "brand": itm.Brand,
            "model": itm.Model,
            "condition": itm.Condition,
            "final_price": float(final_transaction.Price) if final_transaction else None,
            "end_time": auct.EndTime.isoformat() if auct.EndTime else None
        })


    return jsonify(results), 200

@public_bp.route('/browse/item-details/<int:item_id>', methods=['GET'])
@jwt_required()
def get_item_details(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    attributes = ItemAttributeValue.query.filter_by(ItemID=item.ItemID).all()
    attr_data = [{
        "name": Attribute.query.get(attr.AttributeID).Name,
        "value": attr.Value
    } for attr in attributes]

    return jsonify({
        "ItemID": item.ItemID,
        "Title": item.Title,
        "Brand": item.Brand,
        "Model": item.Model,
        "Condition": item.Condition,
        "Description": item.Description,
        "Attributes": attr_data
    }), 200

@public_bp.route('/faq', methods=['GET'])
def get_faqs():
    faqs = FAQ.query.all()
    faq_list = [{"id": faq.FAQID, "question": faq.Question, "answer": faq.Answer} for faq in faqs]
    return jsonify(faq_list), 200



@public_bp.route('/faq/search', methods=['GET'])
def search_faqs():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])

    keywords = query.lower().split()
    faqs = FAQ.query.all()
    results = []

    for faq in faqs:
        question = faq.Question
        answer = faq.Answer
        combined = f"{question} {answer}".lower()

        score = fuzz.partial_ratio(query.lower(), combined)
        if score >= 60:
            highlighted_q = question
            highlighted_a = answer
            for kw in keywords:
                pattern = re.compile(re.escape(kw), re.IGNORECASE)
                highlighted_q = pattern.sub(r'<mark>\g<0></mark>', highlighted_q)
                highlighted_a = pattern.sub(r'<mark>\g<0></mark>', highlighted_a)

            results.append({
                'question': highlighted_q,
                'answer': highlighted_a,
                'score': score
            })

    sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
    return jsonify(sorted_results)

@public_bp.route('/delete-account', methods=['DELETE'])
@jwt_required()
def delete_account():
    """
    Deletes the currently logged-in user's account along with all associated data.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        # Delete associated data
        CustomerQuery.query.filter_by(UserID=user_id).delete()
        Item.query.filter_by(OwnerID=user_id).delete()
        Bid.query.filter_by(UserID=user_id).delete()
        Auction.query.filter(Auction.ItemID.in_(
            db.session.query(Item.ItemID).filter_by(OwnerID=user_id)
        )).delete()

        # Delete the user
        db.session.delete(user)
        db.session.commit()

        return jsonify({"message": "Account and associated data deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        print("🔥 Error deleting account:", str(e))
        return jsonify({"error": "Failed to delete account"}), 500
