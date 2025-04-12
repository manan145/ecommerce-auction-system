from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from ..models import db, User, Transaction, Auction, Item

auction_bp = Blueprint('auction', __name__)

# ================================================
# API → Buyer completes payment for a transaction
# ================================================
@auction_bp.route('/make-payment', methods=['POST'])
@jwt_required()
def make_payment():
    """
    Endpoint: POST /auction/make-payment

    Description:
    Buyer triggers this endpoint to complete payment for a won auction.
    On success:
    - Transaction is marked 'completed'
    - Item ownership is transferred to buyer
    - Item status is set to 'sold'

    Request JSON:
    {
        "transaction_id": 123
    }

    Returns:
        200 OK with transaction details if successful.
        4xx on validation or permission errors.
    """

    current_user_id = get_jwt_identity()
    buyer = User.query.get(current_user_id)
    
    if not buyer or buyer.Role != 'buyer':
        return jsonify({"error": "Only buyers can make payments"}), 403

    data = request.get_json()
    transaction_id = data.get("transaction_id")

    if not transaction_id:
        return jsonify({"error": "Transaction ID is required"}), 400

    # Fetch transaction
    transaction = Transaction.query.get(transaction_id)
    if not transaction:
        return jsonify({"error": "Transaction not found"}), 404

    if transaction.Status != "pending":
        return jsonify({"error": f"Transaction is already '{transaction.Status}'"}), 400

    if transaction.BuyerID != buyer.UserID:
        return jsonify({"error": "You are not authorized to complete this transaction"}), 403

    # Fetch related auction & item
    auction = Auction.query.get(transaction.AuctionID)
    if not auction:
        return jsonify({"error": "Auction not found"}), 404

    item = Item.query.get(auction.ItemID)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    try:
        # Update transaction
        transaction.Status = "completed"
        transaction.TransactionDate = datetime.utcnow()

        # Transfer item ownership
        item.OwnerID = buyer.UserID
        item.Status = "sold"

        db.session.commit()

        return jsonify({
            "message": "Payment successful. Item ownership transferred.",
            "transaction_id": transaction.TransactionID,
            "item_id": item.ItemID,
            "final_price": float(transaction.Price),
            "buyer_id": buyer.UserID
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to complete payment: {str(e)}"}), 500