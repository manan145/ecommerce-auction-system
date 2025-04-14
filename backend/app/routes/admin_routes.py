from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import db, User, CustomerRep, Category, Subcategory, Attribute

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
# Admin – Update Customer Representative profile
# ===========================================
@admin_bp.route('/update-rep', methods=['PUT'])
@jwt_required()
def update_customer_rep():
    current_user_id = get_jwt_identity()
    user = User.query.get(int(current_user_id))
    if not user or user.Role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()
    rep_id = data.get('rep_id')
    if not rep_id:
        return jsonify({'error': 'rep_id is required'}), 400

    rep = CustomerRep.query.get(rep_id)
    if not rep:
        return jsonify({'error': 'Customer Representative not found'}), 404

    # ====== Allow updates ======
    updated = False

    if data.get('department'):
        rep.Department = data['department']
        updated = True

    if data.get('shift'):
        rep.Shift = data['shift']
        updated = True

    if data.get('status'):
        if data['status'] not in ['active', 'inactive']:
            return jsonify({'error': 'Invalid status'}), 400
        rep.Status = data['status']
        updated = True

    if not updated:
        return jsonify({'message': 'No updatable fields provided'}), 400

    db.session.commit()

    return jsonify({"message": "Customer Representative updated successfully"}), 200


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
    category_name = data.get('category_name')
    name = data.get('name')

    if not category_name or not name:
        return jsonify({'error': 'Category name and Subcategory name required'}), 400

    category = Category.query.filter_by(Name=category_name).first()
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

    return jsonify({"categories": category_list}), 200

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
    subcategory_name = data.get('subcategory_name')
    attribute_names = data.get('attributes', [])

    if not subcategory_name or not attribute_names:
        return jsonify({'error': 'Subcategory name and attribute list are required'}), 400

    subcategory = Subcategory.query.filter_by(Name=subcategory_name).first()
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
