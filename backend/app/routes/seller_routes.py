from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import db, User, Item, Subcategory, Attribute, ItemAttributeValue, Auction
from datetime import datetime

from sqlalchemy import and_, or_
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import func


seller_bp = Blueprint('seller', __name__)

# ================================
# Add New Item + Auction + Attributes
# ================================
@seller_bp.route('/add-item', methods=['POST'])
@jwt_required()
def add_item():
    """API → Seller adds new item with required attribute values + auction setup"""
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
        CreatedAt=datetime.utcnow()
    )
    db.session.add(new_item)
    db.session.flush()  # Get ItemID

    # Create Auction
    new_auction = Auction(
        ItemID=new_item.ItemID,
        StartPrice=start_price,
        MinIncrement=min_increment,
        SecretMinPrice=secret_min_price,
        StartTime=datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S'),
        EndTime=datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
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

    db.session.commit()

    return jsonify({
        'message': 'Item and auction added successfully',
        'item_id': new_item.ItemID,
        'auction_id': new_auction.AuctionID
    }), 201


# # ================================
# # View Seller's Items with Attributes
# # ================================
# @seller_bp.route('/my-items', methods=['GET'])
# @jwt_required()
# def view_my_items():
#     """API → Seller views all items including attribute values"""
#     current_user_id = get_jwt_identity()
#     user = User.query.get(current_user_id)

#     if not user or user.Role != 'seller':
#         return jsonify({'error': 'Seller access required'}), 403

#     items = Item.query.filter_by(OwnerID=user.UserID).all()
#     item_list = []

#     for item in items:
#         attrs = ItemAttributeValue.query.filter_by(ItemID=item.ItemID).all()
#         attribute_data = [{
#             "attribute_id": attr.AttributeID,
#             "name": Attribute.query.get(attr.AttributeID).Name,
#             "value": attr.Value
#         } for attr in attrs]

#         item_list.append({
#             "ItemID": item.ItemID,
#             "Title": item.Title,
#             "Description": item.Description,
#             "Brand": item.Brand,
#             "Model": item.Model,
#             "Condition": item.Condition,
#             "SubcategoryID": item.SubcategoryID,
#             "CreatedAt": item.CreatedAt,
#             "Attributes": attribute_data
#         })

#     return jsonify({"items": item_list}), 200


# ================================
# Update Seller's Item + Optional Attributes
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
    return jsonify({'message': 'Item updated successfully'}), 200


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


# # ================================
# # Seller Search items with filters
# # ================================
# @seller_bp.route('/search-items', methods=['GET'])
# @jwt_required()
# def search_items():
#     """API → Seller searches their own items with flexible filters"""
#     current_user_id = get_jwt_identity()
#     user = User.query.get(current_user_id)

#     if not user or user.Role != 'seller':
#         return jsonify({'error': 'Seller access required'}), 403

#     # --- Get query parameters ---
#     title = request.args.get('title')
#     subcategory_name = request.args.get('subcategory_name')
#     attribute_name = request.args.get('attribute_name')
#     value = request.args.get('value')
#     condition = request.args.get('condition')
#     date_from = request.args.get('date_from')
#     date_to = request.args.get('date_to')
#     sort_by = request.args.get('sort_by', 'created_desc')
#     limit = int(request.args.get('limit', 20))
#     offset = int(request.args.get('offset', 0))

#     # --- Start base query for current seller ---
#     query = db.session.query(Item).filter(Item.OwnerID == user.UserID)

#     # --- Filter: title ---
#     if title:
#         query = query.filter(Item.Title.ilike(f"%{title}%"))

#     # --- Filter: subcategory name ---
#     if subcategory_name:
#         query = query.join(Subcategory).filter(Subcategory.Name.ilike(f"%{subcategory_name}%"))

#     # --- Filter: condition ---
#     if condition:
#         query = query.filter(Item.Condition == condition)

#     # --- Filter: date range ---
#     if date_from:
#         try:
#             date_obj = datetime.strptime(date_from, '%Y-%m-%d')
#             query = query.filter(Item.CreatedAt >= date_obj)
#         except:
#             return jsonify({'error': 'Invalid date_from format. Use YYYY-MM-DD'}), 400

#     if date_to:
#         try:
#             date_obj = datetime.strptime(date_to, '%Y-%m-%d')
#             query = query.filter(Item.CreatedAt <= date_obj)
#         except:
#             return jsonify({'error': 'Invalid date_to format. Use YYYY-MM-DD'}), 400

#     # --- Filter: attribute name and value ---
#     if attribute_name and value:
#         query = query.join(ItemAttributeValue, Item.ItemID == ItemAttributeValue.ItemID)\
#                      .join(Attribute, Attribute.AttributeID == ItemAttributeValue.AttributeID)\
#                      .filter(Attribute.Name.ilike(f"%{attribute_name}%"),
#                              ItemAttributeValue.Value.ilike(f"%{value}%"))

#     # --- Sorting ---
#     if sort_by == 'title_asc':
#         query = query.order_by(Item.Title.asc())
#     elif sort_by == 'title_desc':
#         query = query.order_by(Item.Title.desc())
#     else:  # Default to newest first
#         query = query.order_by(Item.CreatedAt.desc())

#     # --- Pagination ---
#     query = query.offset(offset).limit(limit)

#     items = query.all()

#     # --- Build Response ---
#     result = []
#     for item in items:
#         attrs = ItemAttributeValue.query.filter_by(ItemID=item.ItemID).all()
#         attributes = [{
#             "attribute_id": attr.AttributeID,
#             "name": Attribute.query.get(attr.AttributeID).Name,
#             "value": attr.Value
#         } for attr in attrs]

#         result.append({
#             "ItemID": item.ItemID,
#             "Title": item.Title,
#             "Description": item.Description,
#             "Brand": item.Brand,
#             "Model": item.Model,
#             "Condition": item.Condition,
#             "SubcategoryID": item.SubcategoryID,
#             "CreatedAt": item.CreatedAt,
#             "Attributes": attributes
#         })

#     return jsonify({
#         "count": len(result),
#         "results": result
#     }), 200

