from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import db, User, CustomerRep, CustomerQuery, Notification, Auction, Bid, Item, Subcategory
from datetime import datetime, timezone
import json
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

# =========================
# View all open queries
# =========================
@rep_bp.route('/queries', methods=['GET'])
@jwt_required()
def view_queries():
    """
    Customer rep views all open queries (latest first)
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user or user.Role != 'customer_rep':
        return jsonify({'error': 'Unauthorized'}), 403

    queries = CustomerQuery.query.filter_by(Status='open')\
        .order_by(CustomerQuery.CreatedAt.desc()).all()

    return jsonify([{
        'QueryID': q.QueryID,
        'UserID': q.UserID,
        'Subject': q.Subject,
        'Message': q.Message,
        'CreatedAt': q.CreatedAt
    } for q in queries]), 200

# =========================
# Close specific query
# =========================
@rep_bp.route('/queries/close/<int:query_id>', methods=['PUT'])
@jwt_required()
def close_query(query_id):
    """
    Customer rep closes a query after resolution
    """
    rep_id = get_jwt_identity()
    user = User.query.get(rep_id)

    if not user or user.Role != 'customer_rep':
        return jsonify({'error': 'Unauthorized'}), 403

    query = CustomerQuery.query.get(query_id)
    if not query or query.Status == 'closed':
        return jsonify({'error': 'Invalid or already closed query'}), 404

    query.Status = 'closed'

    # notification = Notification(
    #     UserID=query.UserID,
    #     Message=json.dumps({
    #         "type": "query_closed",
    #         "query_id": query.QueryID,
    #         "subject": query.Subject,
    #         "closed_by": rep_id,
    #         "timestamp": datetime.now(timezone.utc)
    #     }),
    # )
    # db.session.add(notification)
    db.session.commit()
    return jsonify({'message': 'Query closed successfully'}), 200

# =========================
# Respond to a specific query
# =========================
@rep_bp.route('/queries/respond/<int:query_id>', methods=['PUT'])
@jwt_required()
def respond_to_query(query_id):
    """
    Customer rep responds to a query
    """
    rep_id = get_jwt_identity()
    user = User.query.get(rep_id)

    if not user or user.Role != 'customer_rep':
        return jsonify({'error': 'Unauthorized'}), 403

    query = CustomerQuery.query.get(query_id)
    if not query or query.Status == 'closed':
        return jsonify({'error': 'Invalid or already closed query'}), 404

    data = request.get_json()
    response = data.get('response')

    if not response:
        return jsonify({'error': 'Response message is required'}), 400

    query.Response = response
    query.ResponseBy = rep_id
    query.ResponseAt = datetime.now(timezone.utc)

    db.session.commit()

    return jsonify({'message': 'Response added successfully'}), 200

# ===========================================================
# Remove Auction
# ===========================================================
@rep_bp.route('/remove-auction/<int:auction_id>', methods=['DELETE'])
@jwt_required()
def remove_auction(auction_id):
    """
    API → Customer rep forcefully deletes an auction record and its associated item from the database.

    Returns:
        200 OK if auction and item are deleted
        404 Not Found if auction does not exist
    """
    auction = Auction.query.get(auction_id)
    if not auction:
        return jsonify({'error': 'Auction not found'}), 404

    # Fetch the associated item
    item = Item.query.get(auction.ItemID)

    db.session.delete(auction)  # Remove the auction

    if item:
        db.session.delete(item)  # Remove the associated item
    db.session.commit()

    return jsonify({'message': f'Auction {auction_id} and its associated item removed successfully.'}), 200


# ===========================================================
# Remove Bid
# ===========================================================
@rep_bp.route('/remove-bid/<int:bid_id>', methods=['DELETE'])
@jwt_required()
def remove_bid(bid_id):
    """
    API → Customer rep removes a specific bid by BidID.

    Returns:
        200 OK if bid is deleted
        404 Not Found if bid does not exist
    """
    bid = Bid.query.get(bid_id)
    if not bid:
        return jsonify({'error': 'Bid not found'}), 404

    db.session.delete(bid)
    db.session.commit()

    return jsonify({'message': f'Bid {bid_id} removed successfully'}), 200

# ================================
# Get All Auctions with Unpacked Item Details
# ================================
@rep_bp.route('/auctions', methods=['GET'])
@jwt_required()
def get_all_auctions():
    """API → Customer Rep fetches all auctions with unpacked item and subcategory details"""
    auctions = Auction.query.all()
    result = []

    for auction in auctions:
        item = Item.query.get(auction.ItemID)
        subcategory = Subcategory.query.get(item.SubcategoryID) if item else None

        result.append({
            'AuctionID': auction.AuctionID,
            'StartPrice': float(auction.StartPrice),
            'MinIncrement': float(auction.MinIncrement),
            'SecretMinPrice': float(auction.SecretMinPrice),
            'StartTime': auction.StartTime.strftime('%Y-%m-%d %H:%M:%S'),
            'EndTime': auction.EndTime.strftime('%Y-%m-%d %H:%M:%S'),
            'IsClosed': auction.IsClosed,
            'ItemID': item.ItemID,
            'Title': item.Title,
            'Brand': item.Brand,
            'Condition': item.Condition,
            'Subcategory': subcategory.Name if subcategory else None,
            'Status': item.Status,
            'CreatedAt': item.CreatedAt.strftime('%Y-%m-%d %H:%M:%S')
        })

    return jsonify(result), 200

# ================================
# Get Bids for Auction by AuctionID
# ================================
@rep_bp.route('/bids/<int:auction_id>', methods=['GET'])
@jwt_required()
def get_bids_for_auction(auction_id):
    """API → Customer Rep fetches all bids for a given auction"""
    bids = Bid.query.filter_by(AuctionID=auction_id).order_by(Bid.BidTime.desc()).all()
    if not bids:
        return jsonify({'message': 'No bids found for this auction'}), 404

    bid_list = [{
        'BidID': bid.BidID,
        'AuctionID': bid.AuctionID,
        'UserID': bid.BidderID,
        'Amount': float(bid.Amount),
        'Timestamp': bid.BidTime.strftime('%Y-%m-%d %H:%M:%S')
    } for bid in bids]

    return jsonify({'bids': bid_list}), 200

# ================================
#  GET user by email
# ================================
@rep_bp.route('/user', methods=['GET', 'POST'])
@jwt_required()
def get_user_by_email_or_id():
    if request.method == 'GET':
        email = request.args.get('email')
        user_id = request.args.get('user_id')
    elif request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        user_id = data.get('user_id')
    else:
        return jsonify({'error': 'Invalid request method'}), 405

    if email:
        user = User.query.filter_by(Email=email).first()
    elif user_id:
        user = User.query.get(user_id)
    else:
        return jsonify({'error': 'Either email or user_id is required'}), 400

    if not user or user.Role not in ['buyer', 'seller']:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'UserID': user.UserID,
        'Username': user.Username,
        'Email': user.Email
    }), 200

# ================================
#  PUT update user
# ================================
@rep_bp.route('/user/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user_info(user_id):
    user = User.query.get(user_id)
    if not user or user.Role not in ['buyer', 'seller']:
        return jsonify({'error': 'User not found'}), 404
    data = request.get_json()
    user.Username = data.get('username', user.Username)
    user.Email = data.get('email', user.Email)
    db.session.commit()
    return jsonify({'message': 'User info updated successfully'}), 200


# 3. DELETE user
@rep_bp.route('/user/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user or user.Role not in ['buyer', 'seller']:
        return jsonify({'error': 'User not found'}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'}), 200