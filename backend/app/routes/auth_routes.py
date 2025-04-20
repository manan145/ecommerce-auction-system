from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from ..models import db, User, Admin
from datetime import datetime, timezone

auth_bp = Blueprint('auth', __name__)

# ========== Register ==========
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data.get('username') or not data.get('email') or not data.get('password') or not data.get('role'):
        return jsonify({"error": "Missing fields"}), 400

    if User.query.filter_by(Email=data['email']).first():
        return jsonify({"error": "Email already exists"}), 409

    hashed_password = generate_password_hash(data['password'])

    new_user = User(
        Username=data['username'],
        Email=data['email'],
        PasswordHash=hashed_password,
        Role=data['role']
    )
    db.session.add(new_user)
    db.session.commit()

    # If Role is Admin, add entry in Admin Table
    if data['role'] == 'admin':
        new_admin = Admin(
            UserID=new_user.UserID,
            AccessLevel='SuperAdmin',  
            CreatedAt=datetime.now(timezone.utc)
        )
        db.session.add(new_admin)
        db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

# ========== Login ==========
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    user = User.query.filter_by(Email=data['email']).first()
    if not user or not check_password_hash(user.PasswordHash, data['password']):
        return jsonify({"error": "Invalid credentials"}), 401
    
    # ===== Update LastLogin for Admin =====
    if user.Role == 'admin':
        admin = Admin.query.filter_by(UserID=user.UserID).first()
        if admin:
            admin.LastLogin = datetime.now(timezone.utc)
            db.session.commit()

    access_token = create_access_token(identity=str(user.UserID))

    return jsonify({
        "message": "Login successful",
        "token": access_token,
        "user": {
            "UserID": user.UserID,
            "Username": user.Username,
            "Email": user.Email,
            "Role": user.Role
        }
    }), 200

# ========== Get Logged in User Profile ==========
@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(int(current_user_id))
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        "UserID": user.UserID,
        "Username": user.Username,
        "Email": user.Email,
        "Role": user.Role,
        "CreatedAt": user.CreatedAt
    }), 200


# ========== Update User Profile ==========

@auth_bp.route('/profile/update', methods=['PUT'])
@jwt_required()
def update_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(int(current_user_id))
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    if data.get('username'):
        user.Username = data['username']
    if data.get('email'):
        existing_user = User.query.filter_by(Email=data['email']).first()
        if existing_user and existing_user.UserID != user.UserID:
            return jsonify({'error': 'Email already exists'}), 409
        user.Email = data['email']

    db.session.commit()
    return jsonify({"message": "Profile updated successfully"}), 200


# ========== Change Password (with Old Password verification) ==========
@auth_bp.route('/profile/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    current_user_id = get_jwt_identity()
    user = User.query.get(int(current_user_id))
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()

    # Validate inputs
    if not data.get('old_password') or not data.get('new_password'):
        return jsonify({'error': 'Missing old or new password'}), 400

    # Verify old password
    if not check_password_hash(user.PasswordHash, data['old_password']):
        return jsonify({'error': 'Incorrect old password'}), 401

    # Update new password
    user.PasswordHash = generate_password_hash(data['new_password'])
    db.session.commit()

    return jsonify({"message": "Password changed successfully"}), 200

# ========== Delete User Account ==========
@auth_bp.route('/profile/delete', methods=['DELETE'])
@jwt_required()
def delete_account():
    current_user_id = get_jwt_identity()
    user = User.query.get(int(current_user_id))
    if not user:
        return jsonify({'error': 'User not found'}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "User account deleted successfully"}), 200
