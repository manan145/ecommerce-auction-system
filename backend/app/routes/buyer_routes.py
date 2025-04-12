from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from ..models import db, Auction, Bid, User, Item
from ..models import db, User, Transaction, Auction, Item

buyer_bp = Blueprint('buyer', __name__)

@buyer_bp.route('/bid', methods=['POST'])
@jwt_required()
def place_bid():
    """
    API Endpoint: POST /bid

    This endpoint lets an authenticated buyer place a bid on an auction.
    It enforces the following rules:
      - Only users with role "buyer" can bid.
      - The auction must exist, be open, and its end time has not passed.
      - Buyers cannot bid on their own items.
      - The bid amount must be at least:
          • If no bids exist: the auction's StartPrice.
          • If there is a current highest bid: current highest bid plus the auction's MinIncrement.
      - The provided max_auto_bid must be at least equal to the bid amount.
      - If the buyer is already the highest bidder, further bids are rejected.
      - After inserting the bid, the system automatically checks for competing bids
        and places auto-bids on behalf of competing buyers (up to their secret maximum).
      - Finally, the final highest bid and winning bidder are returned.
      
    Note: SecretMinPrice is not exposed via this route.
    """
    # -------------------------------
    # 1. Authenticate & Validate Role
    # -------------------------------
    current_user_id = get_jwt_identity()
    buyer = User.query.get(current_user_id)
    if not buyer or buyer.Role != 'buyer':
        return jsonify({"error": "Only buyers can place bids"}), 403

    # -------------------------------
    # 2. Parse Request Data
    # -------------------------------
    data = request.get_json()
    auction_id = data.get("auction_id")
    bid_amount = data.get("amount")
    max_auto_bid = data.get("max_auto_bid") or bid_amount

    if not auction_id or bid_amount is None:
        return jsonify({"error": "Auction ID and bid amount are required"}), 400

    # -------------------------------
    # 3. Retrieve Auction & Validate Timing
    # -------------------------------
    auction = Auction.query.get(auction_id)
    if not auction or auction.IsClosed:
        return jsonify({"error": "Invalid or closed auction"}), 400
    if datetime.utcnow() > auction.EndTime:
        return jsonify({"error": "Auction has ended"}), 400

    # -------------------------------
    # 4. Prevent Buyers from Bidding on Their Own Item
    # -------------------------------
    # Retrieve associated item via auction's ItemID.
    item = Item.query.get(auction.ItemID)
    if not item:
        return jsonify({"error": "Associated item not found"}), 400
    if buyer.UserID == item.OwnerID:
        return jsonify({"error": "You cannot bid on your own item"}), 403

    # -------------------------------
    # 5. Validate Max Auto Bid Input
    # -------------------------------
    if float(max_auto_bid) < float(bid_amount):
        return jsonify({"error": "Maximum auto bid must not be less than the bid amount"}), 400

    # -------------------------------
    # 6. Determine the Minimum Valid Bid
    # -------------------------------
    current_highest = Bid.query.filter_by(AuctionID=auction_id)\
                               .order_by(Bid.Amount.desc()).first()
    # If a bid already exists, new bid must be at least (current highest + MinIncrement)
    if current_highest:
        # Prevent duplicate bid from same user
        if current_highest.BidderID == buyer.UserID:
            return jsonify({"error": "You are already the highest bidder"}), 400
        min_valid_bid = float(current_highest.Amount) + float(auction.MinIncrement)
    else:
        min_valid_bid = float(auction.StartPrice)

    if float(bid_amount) < min_valid_bid:
        return jsonify({"error": f"Your bid must be at least {min_valid_bid}"}), 400

    # -------------------------------
    # 7. Insert the Buyer’s Bid
    # -------------------------------
    new_bid = Bid(
        AuctionID=auction_id,
        BidderID=buyer.UserID,
        Amount=bid_amount,
        MaxAutoBid=float(max_auto_bid),
        BidTime=datetime.utcnow()
    )
    db.session.add(new_bid)
    db.session.flush()  # Flush so we can use new_bid in auto-bid logic

    # Initialize highest bid to the new bid.
    highest_bid = new_bid

    # -------------------------------
    # 8. Automatic Bidding Logic Loop
    # -------------------------------
    # This loop attempts to trigger auto-bids from competing buyers.
    while True:
        # Find the top competing bid from a different bidder whose max_auto_bid is high enough
        competitor = Bid.query.filter(
            Bid.AuctionID == auction_id,
            Bid.BidderID != highest_bid.BidderID,
            Bid.MaxAutoBid > (float(highest_bid.Amount) + float(auction.MinIncrement))
        ).order_by(Bid.MaxAutoBid.desc(), Bid.BidTime.asc()).first()

        # If no competitor qualifies, break the loop.
        if not competitor:
            break

        # Calculate the next bid amount: current highest + minimum increment.
        next_bid_amount = float(highest_bid.Amount) + float(auction.MinIncrement)

        # Automatically place the bid for the competitor.
        auto_bid = Bid(
            AuctionID=auction_id,
            BidderID=competitor.BidderID,
            Amount=next_bid_amount,
            MaxAutoBid=competitor.MaxAutoBid,
            BidTime=datetime.utcnow()
        )
        db.session.add(auto_bid)
        db.session.flush()

        # Update the highest bid to the auto bid.
        highest_bid = auto_bid

    # Commit all changes atomically.
    db.session.commit()

    # -------------------------------
    # 9. Return Final Bid Status
    # -------------------------------
    return jsonify({
        "message": "Bid placed successfully",
        "auction_id": auction_id,
        "final_highest_bid": float(highest_bid.Amount),
        "winning_bidder": highest_bid.BidderID
    }), 201

# ================================================
# API → Buyer completes payment for a transaction
# ================================================
@buyer_bp.route('/make-payment', methods=['POST'])
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