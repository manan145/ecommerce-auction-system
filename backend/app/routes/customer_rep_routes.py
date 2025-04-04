from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import db, User, CustomerRep
from werkzeug.security import generate_password_hash
import string, secrets

rep_bp = Blueprint('rep', __name__)

# =========================
# View Customer Rep Profile
# =========================
@rep_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_rep_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(int(current_user_id))
    if not user or user.Role != 'customer_rep':
        return jsonify({'error': 'Unauthorized'}), 403

    rep = CustomerRep.query.filter_by(UserID=user.UserID).first()
    if not rep:
        return jsonify({'error': 'Rep details not found'}), 404

    return jsonify({
        "RepID": rep.RepID,
        "Username": user.Username,
        "Email": user.Email,
        "Department": rep.Department,
        "Shift": rep.Shift,
        "Status": rep.Status,
        "AssignedBy": rep.AssignedBy
    }), 200

# =========================================
# Customer Rep –  Update profile
# =========================================
@rep_bp.route('/update-profile', methods=['PUT'])
@jwt_required()
def update_rep_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(int(current_user_id))
    if not user or user.Role != 'customer_rep':
        return jsonify({'error': 'Unauthorized'}), 403

    rep = CustomerRep.query.filter_by(UserID=user.UserID).first()
    if not rep:
        return jsonify({'error': 'Customer Representative details not found'}), 404

    data = request.get_json()

    # ====== Allow only Department & Shift update ======
    updated = False

    if data.get('department'):
        rep.Department = data['department']
        updated = True

    if data.get('shift'):
        rep.Shift = data['shift']
        updated = True

    if not updated:
        return jsonify({"message": "No updatable fields provided"}), 400

    db.session.commit()

    return jsonify({"message": "Profile updated successfully"}), 200



# =========================
# Password reset 
# =========================
def generate_temp_password(length=10):
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(characters) for _ in range(length))

@rep_bp.route('/reset-password', methods=['PUT'])
@jwt_required()
def reset_user_password():
    current_user_id = get_jwt_identity()
    rep_user = User.query.get(int(current_user_id))
    if not rep_user or rep_user.Role != 'customer_rep':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    email = data.get('email')

    target_user = User.query.filter_by(Email=email).first()
    if not target_user:
        return jsonify({'error': 'Target user not found'}), 404

    if target_user.Role not in ['buyer', 'seller']:
        return jsonify({'error': 'Password reset allowed only for Buyer/Seller'}), 403

    # Generate Temporary Password
    temp_password = generate_temp_password()

    # Update password
    target_user.PasswordHash = generate_password_hash(temp_password)
    db.session.commit()

    return jsonify({
        "message": f"Temporary password generated for user '{target_user.Username}'",
        "temporary_password": temp_password
    }), 200


