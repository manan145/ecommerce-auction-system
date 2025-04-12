from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from ..models import db, Category, Subcategory, Item, Attribute, ItemAttributeValue, User, Auction
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
# Returns subcategories under a category
# -----------------------------------------------
@public_bp.route('/browse/subcategories/<int:category_id>', methods=['GET'])
def list_subcategories(category_id):
    category = Category.query.get(category_id)
    if not category:
        return jsonify({"error": "Category not found"}), 404

    subcategories = Subcategory.query.filter_by(CategoryID=category_id).all()
    result = [{"SubcategoryID": sub.SubcategoryID, "Name": sub.Name} for sub in subcategories]
    return jsonify(result), 200

# -----------------------------------------------
# GET /browse/items/<subcategory_id>?seller_only=true
# Returns items in a subcategory, optionally filtered by current seller
# -----------------------------------------------
@public_bp.route('/browse/items/<int:subcategory_id>', methods=['GET'])
@jwt_required(optional=True)
def list_items_by_subcategory(subcategory_id):
    user_id = get_jwt_identity()
    seller_only = request.args.get('seller_only', 'false').lower() == 'true'

    query = Item.query.filter(Item.SubcategoryID == subcategory_id)

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
@public_bp.route('/browse/search-items', methods=['POST'])
@jwt_required(optional=True)
def public_search_items():
    data = request.get_json()
    filters = data.get('filters', {})
    sort_by = data.get('sort_by', 'created_desc')
    offset = int(data.get('offset', 0))
    limit = int(data.get('limit', 20))

    # Optional seller-only view
    user_id = get_jwt_identity()
    only_my_items = data.get('only_my_items', False) and user_id is not None

    # Extract auction-related filters
    auction_filters = data.get('auction_filters', {})
    min_price = auction_filters.get('min_price')
    max_price = auction_filters.get('max_price')
    is_closed = auction_filters.get('is_closed')

    # Modify the result to include auction-related filtering
    result = filter_items(
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

    # Add auction details to the result
    for item in result:
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
            if only_my_items:  # Seller can view SecretMinPrice
                auction_data["SecretMinPrice"] = float(auction.SecretMinPrice)
            item["Auction"] = auction_data

    return jsonify(result), 200
