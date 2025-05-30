from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import db, User, CustomerRep, Category, Subcategory, Attribute, Transaction, Auction, Item
from sqlalchemy.sql import func

admin_bp = Blueprint('admin', __name__)

def admin_only():
    current_user_id = get_jwt_identity()
    user = User.query.get(int(current_user_id))
    if user.Role != 'admin':
        return jsonify({"error": "Admin access required"}), 403
    return None

# ====== Create Customer Rep ======
@admin_bp.route('/create-rep', methods=['POST'])
@jwt_required()
def create_customer_rep():
    current_user_id = get_jwt_identity()
    user = User.query.get(int(current_user_id))

    if not user or user.Role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()
    if not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing required fields'}), 400

    if User.query.filter_by(Email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 409

    hashed_password = generate_password_hash(data['password'])

    # Create User
    new_user = User(
        Username=data['username'],
        Email=data['email'],
        PasswordHash=hashed_password,
        Role='customer_rep'
    )
    db.session.add(new_user)
    db.session.commit()

    # Create CustomerRep
    new_rep = CustomerRep(
        UserID=new_user.UserID,
        AssignedBy=user.UserID,
        Department=data.get('department'),
        Shift=data.get('shift'),
        Status='active'
    )
    db.session.add(new_rep)
    db.session.commit()

    return jsonify({'message': 'Customer Representative created successfully'}), 201


# ===========================================
# Admin – View All Customer Representatives
# ===========================================
@admin_bp.route('/customer-reps', methods=['GET'])
@jwt_required()
def get_all_customer_reps():
    current_user_id = get_jwt_identity()
    user = User.query.get(int(current_user_id))
    if not user or user.Role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    reps = CustomerRep.query.all()
    rep_list = []
    for rep in reps:
        rep_user = User.query.get(rep.UserID)
        rep_list.append({
            "RepID": rep.RepID,
            "Username": rep_user.Username,
            "Email": rep_user.Email,
            "Department": rep.Department,
            "Shift": rep.Shift,
            "Status": rep.Status
        })

    return jsonify(rep_list), 200

# ===========================================
# Admin – Delete Customer Representative profile
# ===========================================
@admin_bp.route('/delete-rep/<int:rep_id>', methods=['DELETE'])
@jwt_required()
def delete_customer_rep(rep_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(int(current_user_id))
    if not user or user.Role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    rep = CustomerRep.query.get(rep_id)
    if not rep:
        return jsonify({'error': 'Customer Rep not found'}), 404

    user_account = User.query.get(rep.UserID)
    db.session.delete(rep)
    db.session.delete(user_account)
    db.session.commit()

    return jsonify({'message': 'Customer Rep deleted successfully'}), 200



#============================
# Add category 
#============================
@admin_bp.route('/add-category', methods=['POST'])
@jwt_required()
def add_category():
    current_user_id = get_jwt_identity()
    user = User.query.get(int(current_user_id))
    if not user or user.Role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()
    name = data.get('name')

    if not name:
        return jsonify({'error': 'Category name is required'}), 400

    existing = Category.query.filter_by(Name=name).first()
    if existing:
        return jsonify({'error': 'Category already exists'}), 409

    category = Category(Name=name)
    db.session.add(category)
    db.session.commit()

    return jsonify({'message': 'Category added successfully', 'category_id': category.CategoryID}), 201


#============================
# Add Sub Category
#============================
@admin_bp.route('/add-subcategory', methods=['POST'])
@jwt_required()
def add_subcategory():
    current_user_id = get_jwt_identity()
    user = User.query.get(int(current_user_id))
    if not user or user.Role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()
    category_id = data.get('category_id')
    name = data.get('name')

    if not category_id or not name:
        return jsonify({'error': 'Category name and Subcategory name required'}), 400

    category = Category.query.get(category_id)
    if not category:
        return jsonify({'error': 'Category not found'}), 404

    existing = Subcategory.query.filter_by(Name=name, CategoryID=category.CategoryID).first()
    if existing:
        return jsonify({'error': 'Subcategory already exists in this category'}), 409

    subcategory = Subcategory(Name=name, CategoryID=category.CategoryID)
    db.session.add(subcategory)
    db.session.commit()

    return jsonify({'message': 'Subcategory added successfully', 'subcategory_id': subcategory.SubcategoryID}), 201

#===================================
# List Categories and Sub Categories
#===================================
@admin_bp.route('/categories', methods=['GET'])
def list_categories():
    categories = Category.query.all()
    category_list = []

    for category in categories:
        subcategories = Subcategory.query.filter_by(CategoryID=category.CategoryID).all()
        subcategory_list = [{"SubcategoryID": sub.SubcategoryID, "Name": sub.Name} for sub in subcategories]

        category_list.append({
            "CategoryID": category.CategoryID,
            "Name": category.Name,
            "Subcategories": subcategory_list
        })

    return jsonify(category_list), 200

# ==========================================
# Add Attribute to Subcategory 
# ==========================================
@admin_bp.route('/add-attributes', methods=['POST'])
@jwt_required()
def add_attributes_bulk():
    """Admin adds multiple attributes to a subcategory in one go"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user or user.Role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()
    subcategory_id = data.get('subcategory_id')
    attribute_names = data.get('attributes', [])

    if not subcategory_id or not attribute_names:
        return jsonify({'error': 'Subcategory name and attribute list are required'}), 400

    subcategory = Subcategory.query.get(subcategory_id)
    if not subcategory:
        return jsonify({'error': 'Subcategory not found'}), 404

    added = []
    skipped = []

    for name in attribute_names:
        existing = Attribute.query.filter_by(Name=name, SubcategoryID=subcategory.SubcategoryID).first()
        if not existing:
            attr = Attribute(Name=name, SubcategoryID=subcategory.SubcategoryID)
            db.session.add(attr)
            added.append(name)

    db.session.commit()

    return jsonify({
        "message": "Attribute creation complete",
        "added": added,
        "subcategory_id": subcategory.SubcategoryID
    }), 201

# ==========================================
# Admin – Total Earnings
# ==========================================
@admin_bp.route('/sales-reports/total-earnings', methods=['GET'])
@jwt_required()
def get_total_earnings():
    if error := admin_only():
        return error

    total = db.session.query(func.sum(Transaction.Price)).scalar() or 0
    return jsonify({"total": float(total)}), 200

# ==========================================
# Admin – Earnings per Category (item)
# ==========================================
@admin_bp.route('/sales-reports/earnings-per-item', methods=['GET'])
@jwt_required()
def earnings_per_category():
    if error := admin_only():
        return error

    results = db.session.query(
        Category.Name,
        func.sum(Transaction.Price)
    ).join(Item, Item.CategoryID == Category.CategoryID)\
     .join(Auction, Auction.ItemID == Item.ItemID)\
     .join(Transaction, Transaction.AuctionID == Auction.AuctionID)\
     .group_by(Category.CategoryID).all()

    return jsonify({
        "labels": [r[0] for r in results],
        "values": [float(r[1]) for r in results]
    }), 200

# ==========================================
# Admin – Earnings per Subcategory (item type)
# ==========================================
@admin_bp.route('/sales-reports/earnings-per-item-type', methods=['GET'])
@jwt_required()
def earnings_per_subcategory():
    if error := admin_only():
        return error

    results = db.session.query(
        Subcategory.Name,
        func.sum(Transaction.Price)
    ).join(Item, Item.SubcategoryID == Subcategory.SubcategoryID)\
     .join(Auction, Auction.ItemID == Item.ItemID)\
     .join(Transaction, Transaction.AuctionID == Auction.AuctionID)\
     .group_by(Subcategory.SubcategoryID).all()

    return jsonify({
        "labels": [r[0] for r in results],
        "values": [float(r[1]) for r in results]
    }), 200

# ==========================================
# Admin – Earnings per End-User
# ==========================================
@admin_bp.route('/sales-reports/earnings-per-end-user', methods=['GET'])
@jwt_required()
def earnings_per_user():
    if error := admin_only():
        return error

    results = db.session.query(
        User.Username,
        func.sum(Transaction.Price)
    ).join(User, User.UserID == Transaction.BuyerID)\
     .group_by(User.UserID).all()

    return jsonify({
        "labels": [r[0] for r in results],
        "values": [float(r[1]) for r in results]
    }), 200

# ==========================================
# Admin – Best Selling Items (by count)
# ==========================================
@admin_bp.route('/sales-reports/best-selling-items', methods=['GET'])
@jwt_required()
def best_selling_items():
    if error := admin_only():
        return error

    results = db.session.query(
        Item.Title,
        func.count(Transaction.TransactionID)
    ).join(Auction, Auction.ItemID == Item.ItemID)\
     .join(Transaction, Transaction.AuctionID == Auction.AuctionID)\
     .group_by(Item.ItemID).order_by(func.count(Transaction.TransactionID).desc()).limit(10).all()

    return jsonify({
        "labels": [r[0] for r in results],
        "values": [r[1] for r in results]
    }), 200

# ==========================================
# Admin – Best Buyers (by spend)
# ==========================================
@admin_bp.route('/sales-reports/best-buyers', methods=['GET'])
@jwt_required()
def best_buyers():
    if error := admin_only():
        return error

    results = db.session.query(
        User.Username,
        func.sum(Transaction.Price)
    ).join(User, User.UserID == Transaction.BuyerID)\
     .group_by(User.UserID).order_by(func.sum(Transaction.Price).desc()).limit(10).all()

    return jsonify({
        "labels": [r[0] for r in results],
        "values": [float(r[1]) for r in results]
    }), 200
